import os
import time
import orjson
import asyncio
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query
from fastapi.websockets import WebSocketState
from pydantic import BaseModel
import redis.asyncio as redis
from src.gateways.shared import sentinel
from src.gateways.dependencies import verify_api_key, verify_api_key_in_ws
from src.core.logger import get_console

console = get_console()
router = APIRouter(tags=["observability"])


class DlqDeleteRequest(BaseModel):
    entry: dict


@router.get("/health")
async def health_check():
    """Health check endpoint for Docker/K8s liveness probes."""
    health = {"status": "healthy", "service": "sentinelcell-gateway"}
    try:
        r = redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379/0"))
        await r.ping()
        health["redis"] = "connected"
        await r.aclose()
    except Exception:
        health["redis"] = "disconnected"
        health["status"] = "degraded"
    return health


async def _fetch_metrics_data():
    try:
        r = redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379/0"))
        current_minute = int(time.time() / 60)
        llm_requests = await r.get(f"sentinel:llm_rate_limit:{current_minute}")
        total_requests = await r.get(f"sentinel:total_requests:{current_minute}")
        latency_sum = await r.get(f"sentinel:latency_sum:{current_minute}")
        latency_count = await r.get(f"sentinel:latency_count:{current_minute}")

        llm_req_val = int(llm_requests) if llm_requests else 0
        total_req_val = int(total_requests) if total_requests else 0
        lat_sum_val = float(latency_sum) if latency_sum else 0.0
        lat_cnt_val = int(latency_count) if latency_count else 0
        avg_latency = (lat_sum_val / lat_cnt_val) if lat_cnt_val > 0 else 0.0

        breakers = await sentinel.orchestrator.agent_circuit_breakers.items()
        breakers_dict = {}
        for k, v in breakers:
            if isinstance(v, dict):
                breakers_dict[k] = v
            else:
                breakers_dict[k] = {"failures": v or 0, "last_failure_time": 0.0}

        await r.aclose()
        return {
            "llm_requests_current_min": llm_req_val,
            "llm_rate_limit": int(os.getenv("LLM_RATE_LIMIT_PER_MIN", "50")),
            "max_payload_size": int(os.getenv("MAX_PAYLOAD_SIZE", "102400")),
            "total_requests_current_min": total_req_val,
            "llm_average_latency_ms": avg_latency,
            "agent_circuit_breakers": breakers_dict,
        }
    except Exception as e:
        console.print(f"[bold yellow]Metrics Fetch Error:[/bold yellow] {e}")
        return {
            "llm_requests_current_min": 0,
            "llm_rate_limit": int(os.getenv("LLM_RATE_LIMIT_PER_MIN", "50")),
            "max_payload_size": int(os.getenv("MAX_PAYLOAD_SIZE", "102400")),
            "total_requests_current_min": 0,
            "llm_average_latency_ms": 0.0,
            "agent_circuit_breakers": {},
        }


@router.get("/api/metrics")
async def get_metrics(api_key: str = Depends(verify_api_key)):
    """Returns current rate limit and payload metrics."""
    return await _fetch_metrics_data()


@router.get("/api/audit-logs")
async def get_audit_logs(
    limit: int = 50,
    offset: int = 0,
    search: str | None = None,
    api_key: str = Depends(verify_api_key),
):
    """Returns OTel formatted decisions from the repair logs with pagination and search."""
    log_dir = os.getenv("LOG_DIR", os.path.join(os.getcwd(), "logs"))
    log_path = os.path.join(log_dir, "agent_decisions.json")
    if not os.path.exists(log_path):
        return {"logs": [], "total": 0}

    try:
        raw = ""
        with open(log_path, "r", encoding="utf-8") as f:
            raw = f.read().strip()

        logs = []
        if not raw:
            pass
        elif raw.startswith("["):
            # JSON array format: [{...}, {...}]
            try:
                logs = orjson.loads(raw)
                if not isinstance(logs, list):
                    logs = []
            except orjson.JSONDecodeError:
                logs = []
        else:
            # JSONL format: one JSON object per line
            for line in raw.splitlines():
                line = line.strip()
                if line:
                    try:
                        logs.append(orjson.loads(line))
                    except orjson.JSONDecodeError:
                        continue

        # Normalize timestamps: OTel logs store Timestamp in nanoseconds (19-digit int).
        # JavaScript's Number.MAX_SAFE_INTEGER is ~9×10¹⁵, so values ~1.78×10¹⁸ lose
        # precision when parsed as JSON floats. Convert to ISO string on the backend.
        import datetime

        for log in logs:
            ts_raw = log.get("Timestamp")
            if (
                ts_raw
                and isinstance(ts_raw, (int, float))
                and "TimestampISO" not in log
            ):
                try:
                    # Nanoseconds → seconds → UTC ISO string
                    ts_sec = ts_raw / 1_000_000_000
                    log["TimestampISO"] = (
                        datetime.datetime.fromtimestamp(
                            ts_sec, tz=datetime.timezone.utc
                        ).strftime("%Y-%m-%dT%H:%M:%S.%f")
                        + "Z"
                    )
                except Exception:
                    pass

        if search:
            term = search.lower()
            filtered = []
            for log in logs:
                trace_id = str(log.get("TraceId", "")).lower()
                span_id = str(log.get("SpanId", "")).lower()
                reason = str(log.get("reason", "")).lower()
                attributes = log.get("Attributes") or {}
                source = str(
                    attributes.get("agent.source", log.get("source", ""))
                ).lower()
                target = str(
                    attributes.get("agent.target", log.get("target", ""))
                ).lower()
                decision_id = str(
                    log.get("id", attributes.get("decision.id", ""))
                ).lower()

                if (
                    term in trace_id
                    or term in span_id
                    or term in reason
                    or term in source
                    or term in target
                    or term in decision_id
                ):
                    filtered.append(log)
            logs = filtered

        total_healed = 0
        total_dropped = 0
        for log in logs:
            is_legacy = "TraceId" not in log
            if is_legacy:
                is_healed = "Error" not in log.get("reason", "")
            else:
                is_healed = log.get("SeverityNumber", 0) == 9

            if is_healed:
                total_healed += 1
            else:
                total_dropped += 1

        reversed_logs = logs[::-1]
        return {
            "logs": reversed_logs[offset : offset + limit],
            "total": len(reversed_logs),
            "total_healed": total_healed,
            "total_dropped": total_dropped,
        }
    except Exception as e:
        console.print(f"[bold red]Audit Logs Fetch Error:[/bold red] {e}")
        return {"logs": [], "total": 0}


@router.websocket("/ws/logs")
async def websocket_logs(websocket: WebSocket):
    """Streams live SentinelCell logs from Redis PubSub to connected WebSockets"""
    await websocket.accept()
    await verify_api_key_in_ws(websocket)

    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
    try:
        client = redis.from_url(redis_url)
        pubsub = client.pubsub()
        await pubsub.subscribe("sentinel.logs")

        while True:
            message = await pubsub.get_message(
                ignore_subscribe_messages=True, timeout=1.0
            )
            if message:
                await websocket.send_text(message["data"].decode("utf-8"))
            await asyncio.sleep(0.1)
    except WebSocketDisconnect:
        try:
            await pubsub.unsubscribe("sentinel.logs")
        except Exception as unsubscribe_err:
            console.print(
                f"[bold red]WebSocket pubsub unsubscribe error:[/bold red] {unsubscribe_err}"
            )
    except Exception as e:
        if websocket.client_state == WebSocketState.CONNECTED:
            try:
                await websocket.send_text(
                    orjson.dumps({"type": "SYSTEM_ERROR", "content": str(e)}).decode(
                        "utf-8"
                    )
                )
            except Exception as send_err:
                console.print(
                    f"[bold red]WebSocket error sending SYSTEM_ERROR:[/bold red] {send_err}"
                )


@router.get("/api/dlq")
async def get_dlq_logs(
    limit: int = Query(default=50, ge=1, le=500),
    offset: int = Query(default=0, ge=0, le=10000),
    api_key: str = Depends(verify_api_key),
):
    """Returns all payloads currently in the Dead Letter Queue (DLQ) for the UI."""
    logs = []
    seen_signatures = set()

    # Merge from all possible DLQ persistence layers to match runtime write behavior.
    dlq_dir = os.getenv("LOG_DIR", os.path.join(os.getcwd(), "logs"))
    dlq_path = os.path.join(dlq_dir, "dlq.json")
    if os.path.exists(dlq_path):
        try:
            with open(dlq_path, "r", encoding="utf-8") as f:
                for line in f:
                    _append_entry(line, logs, seen_signatures)
        except Exception as e:
            console.print(f"[bold red]DLQ file read error:[/bold red] {e}")

    # Read enough records for requested page while keeping an upper bound.
    fetch_size = min(max(limit + offset, 500), 5000)

    provider = os.getenv("MESSAGE_BROKER", "REDIS").upper()
    if provider == "REDIS":
        redis_client = None
        try:
            redis_client = redis.from_url(
                os.getenv("REDIS_URL", "redis://localhost:6379/0"),
                decode_responses=False,
            )
            redis_entries = await redis_client.lrange("sentinel.dlq", 0, fetch_size - 1)
            for entry in redis_entries:
                _append_entry(entry, logs, seen_signatures)
        except Exception as e:
            console.print(f"[bold yellow]DLQ Redis fetch error:[/bold yellow] {e}")
        finally:
            if redis_client is not None:
                try:
                    await redis_client.aclose()
                except Exception:
                    pass

    pg_uri = os.getenv("POSTGRES_URI") or os.getenv("SCHEMA_POSTGRES_URI")
    if pg_uri:
        try:
            import psycopg2

            conn = psycopg2.connect(pg_uri)
            cur = conn.cursor()
            cur.execute(
                "SELECT entry FROM sentinel_dlq_fallback ORDER BY created_at DESC LIMIT %s",
                (fetch_size,),
            )
            for (entry,) in cur.fetchall():
                _append_entry(entry, logs, seen_signatures)
            cur.close()
            conn.close()
        except Exception as e:
            console.print(f"[bold yellow]DLQ Postgres fetch error:[/bold yellow] {e}")

    sorted_logs = sorted(logs, key=_ts, reverse=True)
    return {
        "logs": sorted_logs[offset : offset + limit],
        "total": len(sorted_logs),
        "limit": limit,
        "offset": offset,
    }


@router.post("/api/dlq/delete")
async def delete_dlq_item(
    req: DlqDeleteRequest,
    api_key: str = Depends(verify_api_key),
):
    """Deletes matching DLQ entry from all supported persistence layers."""
    target = req.entry
    removed = {"redis": 0, "file": 0, "postgres": 0}

    provider = os.getenv("MESSAGE_BROKER", "REDIS").upper()
    if provider == "REDIS":
        redis_client = None
        try:
            redis_client = redis.from_url(
                os.getenv("REDIS_URL", "redis://localhost:6379/0"),
                decode_responses=False,
            )
            redis_entries = await redis_client.lrange("sentinel.dlq", 0, -1)
            for raw_entry in redis_entries:
                try:
                    parsed = orjson.loads(raw_entry)
                    if parsed == target:
                        removed["redis"] += await redis_client.lrem(
                            "sentinel.dlq", 1, raw_entry
                        )
                except Exception:
                    continue
        except Exception as e:
            console.print(f"[bold yellow]DLQ Redis delete error:[/bold yellow] {e}")
        finally:
            if redis_client is not None:
                try:
                    await redis_client.aclose()
                except Exception:
                    pass

    dlq_dir = os.getenv("LOG_DIR", os.path.join(os.getcwd(), "logs"))
    dlq_path = os.path.join(dlq_dir, "dlq.json")
    if os.path.exists(dlq_path):
        try:
            retained_lines = []
            with open(dlq_path, "r", encoding="utf-8") as f:
                for line in f:
                    stripped = line.strip()
                    if not stripped:
                        continue
                    try:
                        parsed = orjson.loads(stripped)
                        if parsed == target:
                            removed["file"] += 1
                            continue
                    except Exception:
                        pass
                    retained_lines.append(line)
            with open(dlq_path, "w", encoding="utf-8") as f:
                f.writelines(retained_lines)
        except Exception as e:
            console.print(f"[bold yellow]DLQ file delete error:[/bold yellow] {e}")

    pg_uri = os.getenv("POSTGRES_URI") or os.getenv("SCHEMA_POSTGRES_URI")
    if pg_uri:
        try:
            import psycopg2
            from psycopg2.extras import Json

            conn = psycopg2.connect(pg_uri)
            cur = conn.cursor()
            cur.execute(
                "DELETE FROM sentinel_dlq_fallback WHERE entry = %s::jsonb",
                (Json(target),),
            )
            removed["postgres"] = cur.rowcount or 0
            conn.commit()
            cur.close()
            conn.close()
        except Exception as e:
            console.print(f"[bold yellow]DLQ Postgres delete error:[/bold yellow] {e}")

    total_removed = removed["redis"] + removed["file"] + removed["postgres"]
    return {"status": "success", "removed": removed, "total_removed": total_removed}


def _ts(entry):
    try:
        return float(entry.get("timestamp", 0))
    except Exception:
        return 0.0


def _append_entry(raw_entry, logs, seen_signatures):
    if isinstance(raw_entry, (bytes, bytearray)):
        raw_entry = raw_entry.decode("utf-8", errors="replace")
    if isinstance(raw_entry, str):
        raw_entry = raw_entry.strip()
        if not raw_entry:
            return
        try:
            raw_entry = orjson.loads(raw_entry)
        except orjson.JSONDecodeError as decode_err:
            console.print(
                f"[dim yellow]DLQ parse error:[/dim yellow] {raw_entry} - {decode_err}"
            )
            return
    if not isinstance(raw_entry, dict):
        return

    try:
        signature = orjson.dumps(raw_entry, option=orjson.OPT_SORT_KEYS)
    except Exception:
        signature = str(raw_entry)

    if signature in seen_signatures:
        return
    seen_signatures.add(signature)
    logs.append(raw_entry)
