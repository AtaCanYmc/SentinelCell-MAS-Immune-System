import os
import orjson
import asyncio
import time
import dotenv
import json
from pydantic import BaseModel
from contextlib import asynccontextmanager
from fastapi import (
    FastAPI,
    Request,
    HTTPException,
    WebSocket,
    WebSocketDisconnect,
    Depends,
    Header,
    Cookie,
)
from fastapi.responses import JSONResponse
from src.core.logger import get_console

from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import redis.asyncio as redis
from src.agents.validator_agent import SentinelCell
from prometheus_client import make_asgi_app
from src.core.session_manager import create_session_token, verify_session_token
from src.gateways.constants import SAFE_SCRIPTS

console = get_console()


# Startup Environment and Credential Validation (Fail-Fast Policy)
def _validate_startup_config():
    import sys

    if "pytest" in sys.modules:
        return

    # 1. Base requirements
    redis_url = os.getenv("REDIS_URL")
    if not redis_url:
        console.print(
            "[bold yellow][!] Warning: REDIS_URL not set. Running with local fallback state.[/bold yellow]"
        )

    # 2. Schema Registry requirements
    registry_provider = os.getenv("SCHEMA_REGISTRY_PROVIDER", "REDIS").upper()
    if registry_provider == "SUPABASE":
        if not os.getenv("SUPABASE_URL") or not os.getenv("SUPABASE_KEY"):
            raise ValueError(
                "SCHEMA_REGISTRY_PROVIDER is SUPABASE, but SUPABASE_URL or SUPABASE_KEY is missing."
            )
    elif registry_provider == "POSTGRES":
        if not os.getenv("SCHEMA_POSTGRES_URI") and not os.getenv("POSTGRES_URI"):
            raise ValueError(
                "SCHEMA_REGISTRY_PROVIDER is POSTGRES, but SCHEMA_POSTGRES_URI or POSTGRES_URI is missing."
            )

    # 3. Vector DB requirements
    vector_provider = os.getenv("VECTOR_DB_PROVIDER", "CHROMADB").upper()
    if vector_provider == "PINECONE":
        if not os.getenv("PINECONE_API_KEY"):
            raise ValueError(
                "VECTOR_DB_PROVIDER is PINECONE, but PINECONE_API_KEY is missing."
            )
    elif vector_provider == "PGVECTOR":
        if not os.getenv("POSTGRES_URI"):
            raise ValueError(
                "VECTOR_DB_PROVIDER is PGVECTOR, but POSTGRES_URI is missing."
            )

    # 4. LLM Providers API Keys validation
    providers_str = os.getenv("PROVIDER_ORDER", "OPENAI,LOCAL_OLLAMA,ANTHROPIC,GROQ")
    providers = [p.strip().upper() for p in providers_str.split(",") if p.strip()]
    for provider in providers:
        if provider == "OPENAI" and not os.getenv("OPENAI_API_KEY"):
            raise ValueError(
                "LLM provider list contains OPENAI, but OPENAI_API_KEY is missing."
            )
        elif provider == "ANTHROPIC" and not os.getenv("ANTHROPIC_API_KEY"):
            raise ValueError(
                "LLM provider list contains ANTHROPIC, but ANTHROPIC_API_KEY is missing."
            )
        elif provider == "GROQ" and not os.getenv("GROQ_API_KEY"):
            raise ValueError(
                "LLM provider list contains GROQ, but GROQ_API_KEY is missing."
            )
        elif provider == "GEMINI" and not os.getenv("GEMINI_API_KEY"):
            raise ValueError(
                "LLM provider list contains GEMINI, but GEMINI_API_KEY is missing."
            )
        elif provider == "DEEPSEEK" and not os.getenv("DEEPSEEK_API_KEY"):
            raise ValueError(
                "LLM provider list contains DEEPSEEK, but DEEPSEEK_API_KEY is missing."
            )


_validate_startup_config()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    try:
        await sentinel.mcp_client.start()
    except Exception as e:
        console.print(
            f"[bold red]Failed to start persistent MCP client: {e}[/bold red]"
        )
    yield
    # Shutdown
    try:
        await sentinel.stop()
    except Exception as e:
        console.print(f"[bold red]Failed to stop persistent MCP client: {e}[/bold red]")


app = FastAPI(
    title="SentinelCell Guardian Gateway",
    description="Transparent API Gateway and Live Dashboard for Multi-Agent Systems",
    lifespan=lifespan,
)
sentinel = SentinelCell()


@app.get("/health")
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


@app.get("/dashboard")
async def dashboard_ui():
    """Lightweight health/placeholder route so the test-suite and simple
    deployments can probe the dashboard entrypoint. The real dashboard is
    served by the separate frontend container in production setups.
    """
    return JSONResponse(content={"status": "ok", "page": "dashboard"})


security = HTTPBearer(auto_error=False)


def verify_api_key(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    sentinel_session: str | None = Cookie(None),
):
    expected_api_key = os.getenv("API_KEY_SECRET")
    if not expected_api_key:
        return True

    # 1. Check for cookie-based session token
    if sentinel_session:
        username = verify_session_token(sentinel_session)
        if username:
            return username

    # 2. Check for Bearer token (API_KEY_SECRET)
    if credentials and credentials.credentials == expected_api_key:
        return credentials.credentials

    # If neither matches
    raise HTTPException(status_code=401, detail="Invalid or missing API Key or Session")


class LoginRequest(BaseModel):
    username: str
    password: str


@app.post("/api/auth/login")
async def login(req: LoginRequest):
    expected_user = os.getenv("DASHBOARD_USERNAME", "admin")
    expected_pass = os.getenv("DASHBOARD_PASSWORD", "sentinel")

    if req.username != expected_user or req.password != expected_pass:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_session_token(req.username)
    response = JSONResponse(content={"status": "success", "username": req.username})
    response.set_cookie(
        key="sentinel_session",
        value=token,
        httponly=True,
        max_age=3600,
        samesite="lax",
        secure=False,
    )
    return response


@app.post("/api/auth/logout")
async def logout():
    response = JSONResponse(content={"status": "success"})
    response.delete_cookie(key="sentinel_session")
    return response


# Add Prometheus metrics route
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)


@app.websocket("/ws/logs")
async def websocket_logs(websocket: WebSocket):
    """Streams live SentinelCell logs from Redis PubSub to connected WebSockets"""
    await websocket.accept()

    # First Message Auth: client sends {"type": "AUTH", "token": "..."} as first message
    expected_api_key = os.getenv("API_KEY_SECRET")
    if expected_api_key:
        session_cookie = websocket.cookies.get("sentinel_session")
        has_valid_cookie = (
            session_cookie and verify_session_token(session_cookie) is not None
        )
        if not has_valid_cookie:
            try:
                auth_msg = await asyncio.wait_for(
                    websocket.receive_text(), timeout=10.0
                )
                auth_data = orjson.loads(auth_msg)
                if (
                    auth_data.get("type") != "AUTH"
                    or auth_data.get("token") != expected_api_key
                ):
                    await websocket.send_text(
                        orjson.dumps({"type": "AUTH_FAILED"}).decode("utf-8")
                    )
                    await websocket.close(code=1008)
                    return
            except (asyncio.TimeoutError, Exception):
                await websocket.close(code=1008)
                return

    redis_url = os.getenv("REDIS_URL", "redis://redis:6379")
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


@app.post("/intercept")
async def intercept_traffic(
    source: str,
    target: str,
    request: Request,
    api_key: str = Depends(verify_api_key),
    x_idempotency_key: str = Header(None),
):
    """
    HTTP Endpoint acting as the Guardian Gateway.
    Legacy agents can POST their payloads here to be scrubbed by the Immune System.
    """
    try:
        raw_body = (await request.body()).decode("utf-8")

        redis_url = os.getenv("REDIS_URL")
        r = None
        if x_idempotency_key and redis_url:
            try:
                r = redis.from_url(redis_url)
                idem_key = f"idempotency:{x_idempotency_key}"

                # ATOMIC SET NX: A fully atomic operation—other requests cannot interfere in the meantime
                # If the Redis SETNX command (SET if Not eXists) returns true,
                # we proceed; if it returns false, it means another request has already processed it.
                was_set = await r.set(idem_key, "PROCESSING", ex=86400, nx=True)

                if not was_set:
                    # If another request is processing the same idempotency key,
                    # subscribe to its completion channel instead of busy-waiting.
                    channel = f"sentinel:idem:channel:{x_idempotency_key}"
                    pubsub = r.pubsub()
                    await pubsub.subscribe(channel)
                    try:
                        start_wait = time.time()
                        timeout = int(os.getenv("IDEMPOTENCY_WAIT_SECONDS", "30"))
                        while time.time() - start_wait < timeout:
                            msg = await pubsub.get_message(
                                ignore_subscribe_messages=True, timeout=1.0
                            )
                            if msg and msg.get("data"):
                                try:
                                    payload = (
                                        orjson.loads(msg["data"])
                                        if isinstance(msg["data"], (bytes, str))
                                        else msg["data"]
                                    )
                                except Exception:
                                    payload = None
                                if payload:
                                    return JSONResponse(
                                        status_code=208, content=payload
                                    )
                            await asyncio.sleep(0.1)
                    finally:
                        try:
                            await pubsub.unsubscribe(channel)
                        except Exception:
                            pass
                    # Timeout waiting for master result
                    raise HTTPException(
                        status_code=409,
                        detail="Idempotent request already in progress. Please retry.",
                    )
            except Exception as redis_err:
                console.print(
                    f"[bold yellow]Redis idempotency read error:[/bold yellow] {redis_err}"
                )

        result = await sentinel.intercept(
            source=source, target=target, payload=raw_body
        )

        if result is None:
            raise HTTPException(
                status_code=400,
                detail="Payload rejected or unrecoverable by SentinelCell.",
            )

        if x_idempotency_key and r:
            try:
                await r.setex(
                    idem_key,
                    86400,
                    orjson.dumps(result).decode("utf-8"),
                )
                # Notify any subscribers waiting on this idempotency key
                try:
                    await r.publish(
                        f"sentinel:idem:channel:{x_idempotency_key}",
                        orjson.dumps(result).decode("utf-8"),
                    )
                except Exception:
                    pass
            except Exception as redis_set_err:
                console.print(
                    f"[bold yellow]Redis idempotency write error:[/bold yellow] {redis_set_err}"
                )

        return result
    except HTTPException:
        raise
    except json.JSONDecodeError as json_err:
        console.print(f"[bold yellow]Payload Parsing Error:[/bold yellow] {json_err}")
        raise HTTPException(
            status_code=400,
            detail="Invalid request payload format. Ensure valid JSON.",
        )
    except asyncio.TimeoutError:
        console.print("[bold red]Request Processing Timeout[/bold red]")
        raise HTTPException(
            status_code=504,
            detail="Request processing exceeded timeout. Please try again.",
        )
    except Exception as e:
        console.print(f"[bold red]Intercept Error:[/bold red] {e}")
        raise HTTPException(
            status_code=500,
            detail="Payload processing failed. Check server logs for details.",
        )


class ChatRequest(BaseModel):
    message: str


@app.post("/chat/test")
async def chat_test(req: ChatRequest, api_key: str = Depends(verify_api_key)):
    """
    Direct endpoint to test the configured LLM models.
    """
    try:
        from src.core.llm_factory import LLMFactory

        provider = os.getenv("PROVIDER_ORDER", "OPENAI").split(",")[0].strip()
        llm = LLMFactory.get_llm(provider)
        response = await llm.ainvoke(req.message)
        return {
            "status": "success",
            "response": response.content,
            "provider": provider,
        }
    except ValueError as ve:
        console.print(f"[bold yellow]LLM Configuration Error:[/bold yellow] {ve}")
        raise HTTPException(
            status_code=400,
            detail="LLM provider is not properly configured.",
        )
    except Exception as e:
        console.print(f"[bold red]Chat Test Error:[/bold red] {e}")
        raise HTTPException(
            status_code=500,
            detail="LLM request failed. Check server logs for details.",
        )


@app.websocket("/ws/chat")
async def websocket_chat(
    websocket: WebSocket,
    lang: str = "en",
    provider: str | None = None,
):
    """
    WebSocket endpoint for real-time LLM chat streaming.
    """
    await websocket.accept()

    # First Message Auth
    expected_api_key = os.getenv("API_KEY_SECRET")
    if expected_api_key:
        session_cookie = websocket.cookies.get("sentinel_session")
        has_valid_cookie = (
            session_cookie and verify_session_token(session_cookie) is not None
        )
        if not has_valid_cookie:
            try:
                auth_msg = await asyncio.wait_for(
                    websocket.receive_text(), timeout=10.0
                )
                auth_data = orjson.loads(auth_msg)
                if (
                    auth_data.get("type") != "AUTH"
                    or auth_data.get("token") != expected_api_key
                ):
                    await websocket.send_text(
                        orjson.dumps({"type": "AUTH_FAILED"}).decode("utf-8")
                    )
                    await websocket.close(code=1008)
                    return
            except (asyncio.TimeoutError, Exception):
                await websocket.close(code=1008)
                return

    if not provider:
        provider = os.getenv("PROVIDER_ORDER", "OPENAI").split(",")[0].strip()

    try:
        from src.services.chat_service import ChatService

        await ChatService.handle_websocket_chat(websocket, sentinel, provider, lang)
    except WebSocketDisconnect:
        pass
    except Exception as e:
        console.print(f"[bold red]WebSocket chat error:[/bold red] {e}")
        try:
            await websocket.send_text(
                orjson.dumps({"type": "error", "content": str(e)}).decode("utf-8")
            )
        except Exception:
            pass


@app.delete("/memory/purge")
async def purge_memory(days: int = 30, api_key: str = Depends(verify_api_key)):
    """
    Purges old hallucination corrections from the VectorDB
    to prevent memory bloat and maintain optimal RAG performance.
    """
    try:
        from src.core.memory_factory import MemoryFactory

        if days <= 0:
            raise ValueError("days parameter must be positive")
        memory_store = MemoryFactory.get_memory_store()
        deleted_count = memory_store.purge_old_memories(days=days)
        return {
            "status": "success",
            "message": f"Purged memories older than {days} days.",
            "deleted_count": deleted_count,
        }
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        console.print(f"[bold red]Memory Purge Error:[/bold red] {e}")
        raise HTTPException(
            status_code=500,
            detail="Memory purge operation failed. Check server logs for details.",
        )


@app.post("/schema/refresh")
async def refresh_schema(
    agent_target: str = None, api_key: str = Depends(verify_api_key)
):
    """
    Purges the local schema cache for a specific agent, or all agents if none provided.
    This guarantees instant consistency for the next payload without waiting for TTL.
    """
    try:
        if agent_target:
            sentinel.validator.clear_cache(agent_target)
            return {
                "status": "success",
                "message": f"Schema cache cleared for {agent_target}",
            }
        else:
            sentinel.validator.clear_cache()
            return {"status": "success", "message": "All schema caches cleared"}
    except Exception as e:
        console.print(f"[bold red]Schema Refresh Error:[/bold red] {e}")
        raise HTTPException(
            status_code=500,
            detail="An internal error occurred. Check server logs for details.",
        )


@app.get("/api/schemas")
async def get_all_schemas(api_key: str = Depends(verify_api_key)):
    """Returns all schemas currently stored in the active Registry Store."""
    try:
        from src.core.registry_factory import RegistryFactory

        store = RegistryFactory.get_registry_store()
        schemas = await store.get_all_schemas()
        # The schemas are stored as JSON strings in the registry,
        # so we load them back into dicts to return a clean JSON response.
        return {
            agent_id: orjson.loads(schema_str)
            if isinstance(schema_str, str)
            else schema_str
            for agent_id, schema_str in schemas.items()
        }
    except Exception as e:
        console.print(f"[bold red]Schema Fetch Error:[/bold red] {e}")
        raise HTTPException(
            status_code=500,
            detail="An internal error occurred. Check server logs for details.",
        )


@app.get("/api/config")
async def get_config(api_key: str = Depends(verify_api_key)):
    """Returns all environment variables for the settings dashboard."""
    env_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))), ".env"
    )
    config = dotenv.dotenv_values(env_path)
    return {k: v if v is not None else "" for k, v in config.items()}


@app.post("/api/config")
async def update_config(config: dict[str, str], api_key: str = Depends(verify_api_key)):
    """Updates .env file with new configurations."""
    env_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))), ".env"
    )

    if not os.path.exists(env_path):
        open(env_path, "a").close()

    updated = {}
    for key, value in config.items():
        if value is not None:
            dotenv.set_key(env_path, key, str(value))
            updated[key] = value
            os.environ[key] = str(value)

    return {"status": "success", "updated": updated}


@app.get("/api/dlq")
async def get_dlq(api_key: str = Depends(verify_api_key)):
    """Returns the Dead Letter Queue logs for the Quarantine UI."""
    log_dir = os.getenv("LOG_DIR", os.path.join(os.getcwd(), "logs"))
    dlq_path = os.path.join(log_dir, "dlq.json")
    if not os.path.exists(dlq_path):
        return []

    logs = []
    with open(dlq_path, "r") as f:
        for line in f:
            if line.strip():
                try:
                    logs.append(orjson.loads(line))
                except orjson.JSONDecodeError as decode_err:
                    console.print(
                        f"[dim yellow]DLQ log parse error on line:[/dim yellow] {line.strip()} - {decode_err}"
                    )
    # Return latest first
    return logs[::-1]


class ReplayRequest(BaseModel):
    source: str
    target: str
    payload: str


@app.get("/api/agents")
async def get_agents(api_key: str = Depends(verify_api_key)):
    """Returns the current state of agent circuit breakers."""
    import time

    threshold = int(os.getenv("CIRCUIT_BREAKER_THRESHOLD", "5"))
    cooldown = int(os.getenv("CIRCUIT_BREAKER_COOLDOWN", "60"))
    breakers = sentinel.orchestrator.agent_circuit_breakers
    result = []
    for agent, errors in breakers.items():
        failures = (
            errors.get("failures", 0) if isinstance(errors, dict) else (errors or 0)
        )
        last_failure = (
            errors.get("last_failure_time", 0.0) if isinstance(errors, dict) else 0.0
        )

        status = "HEALTHY"
        if failures >= threshold:
            if time.time() - last_failure > cooldown:
                status = "RECOVERING"
            else:
                status = "TRIPPED"

        result.append(
            {
                "id": agent,
                "errors": errors,
                "status": status,
                "threshold": threshold,
                "last_failure_time": last_failure,
                "cooldown": cooldown,
            }
        )
    return {"agents": result}


@app.post("/api/agents/{agent_id}/reset")
async def reset_agent(agent_id: str, api_key: str = Depends(verify_api_key)):
    if agent_id in sentinel.orchestrator.agent_circuit_breakers:
        sentinel.orchestrator.agent_circuit_breakers[agent_id] = {
            "failures": 0,
            "last_failure_time": 0.0,
        }
    return {"status": "ok", "agent": agent_id, "errors": 0}


@app.get("/api/metrics")
async def get_metrics(api_key: str = Depends(verify_api_key)):
    """Returns current rate limit and payload metrics."""
    try:
        r = redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379/0"))
        current_minute = int(time.time() / 60)
        llm_requests = await r.get(f"sentinel:llm_rate_limit:{current_minute}")
        return {
            "llm_requests_current_min": int(llm_requests) if llm_requests else 0,
            "llm_rate_limit": int(os.getenv("LLM_RATE_LIMIT_PER_MIN", "50")),
            "max_payload_size": int(os.getenv("MAX_PAYLOAD_SIZE", "102400")),
        }
    except Exception as e:
        console.print(f"[bold yellow]Metrics Fetch Error:[/bold yellow] {e}")
        return {
            "llm_requests_current_min": 0,
            "llm_rate_limit": int(os.getenv("LLM_RATE_LIMIT_PER_MIN", "50")),
            "max_payload_size": int(os.getenv("MAX_PAYLOAD_SIZE", "102400")),
        }


@app.get("/api/audit-logs")
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
        with open(log_path, "r") as f:
            logs = orjson.loads(f.read())

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

        reversed_logs = logs[::-1]
        return {
            "logs": reversed_logs[offset : offset + limit],
            "total": len(reversed_logs),
        }
    except Exception as e:
        console.print(f"[bold red]Audit Logs Fetch Error:[/bold red] {e}")
        return {"logs": [], "total": 0}


class HITLApprovalRequest(BaseModel):
    approval_id: str
    decision: str  # "APPROVED" or "REJECTED"


@app.post("/api/hitl/approval")
async def submit_hitl_approval(
    req: HITLApprovalRequest, api_key: str = Depends(verify_api_key)
):
    """
    Submits HITL (Human-in-the-Loop) approval decision.
    Dashboard operatörü "Approve" veya "Reject" butonuna bastığında bu endpoint'i çağırır.
    """
    try:
        if req.decision not in ["APPROVED", "REJECTED"]:
            raise HTTPException(
                status_code=400,
                detail="Decision must be 'APPROVED' or 'REJECTED'",
            )

        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        r = redis.from_url(redis_url)

        # Redis'den HITL pending state'ini alıp güncelle
        hitl_key = f"sentinel:hitl:{req.approval_id}"
        approval_data = await r.get(hitl_key)

        if not approval_data:
            raise HTTPException(
                status_code=404,
                detail="HITL approval ID not found or expired",
            )

        # Decision'ı kaydet
        data = orjson.loads(approval_data)
        data["status"] = req.decision
        data["decided_at"] = time.time()

        await r.setex(
            hitl_key,
            300,  # 5 minute TTL
            orjson.dumps(data).decode("utf-8"),
        )

        # Notify dashboard via Redis PubSub
        await r.publish(
            "sentinel.logs",
            orjson.dumps(
                {
                    "type": "HITL_DECISION",
                    "approval_id": req.approval_id,
                    "decision": req.decision,
                }
            ).decode("utf-8"),
        )

        # Also notify the orchestrator (or any waiter) via the HITL decision channel
        try:
            await r.publish(
                f"sentinel:hitl:channel:{req.approval_id}",
                orjson.dumps(data).decode("utf-8"),
            )
        except Exception:
            pass

        await r.aclose()

        return {
            "status": "success",
            "message": f"HITL approval {req.decision}",
            "approval_id": req.approval_id,
        }

    except HTTPException:
        raise
    except Exception as e:
        console.print(f"[bold red]HITL Approval Error:[/bold red] {e}")
        raise HTTPException(
            status_code=500,
            detail="HITL approval submission failed. Check server logs for details.",
        )


@app.post("/api/dlq/replay")
async def replay_payload(req: ReplayRequest, api_key: str = Depends(verify_api_key)):
    """Manually replays a payload from the Quarantine UI."""
    try:
        result = await sentinel.intercept(
            source=req.source, target=req.target, payload=req.payload
        )
        if result is None:
            raise HTTPException(
                status_code=400,
                detail="Replay failed. Payload was rejected again.",
            )
        return {"status": "success", "result": result}
    except HTTPException:
        raise
    except Exception as e:
        console.print(f"[bold red]DLQ Replay Error:[/bold red] {e}")
        raise HTTPException(
            status_code=500,
            detail="An internal error occurred. Check server logs for details.",
        )


@app.get("/api/examples")
async def list_examples(api_key: str = Depends(verify_api_key)):
    """Lists available interactive simulation examples with description."""
    json_path = os.path.join("examples", "examples.json")
    if not os.path.exists(json_path):
        return {"examples": []}
    try:
        with open(json_path, "r", encoding="utf-8") as f:
            examples = orjson.loads(f.read())
        return {"examples": examples}
    except Exception as e:
        console.print(f"[bold red]Error reading examples.json:[/bold red] {e}")
        return {"examples": []}


@app.websocket("/ws/examples/run/{script_name}")
async def ws_run_example(websocket: WebSocket, script_name: str):
    """Runs a simulation script and streams stdout/stderr back in real-time."""
    await websocket.accept()

    # First Message Auth
    expected_api_key = os.getenv("API_KEY_SECRET")
    if expected_api_key:
        session_cookie = websocket.cookies.get("sentinel_session")
        has_valid_cookie = (
            session_cookie and verify_session_token(session_cookie) is not None
        )
        if not has_valid_cookie:
            try:
                auth_msg = await asyncio.wait_for(
                    websocket.receive_text(), timeout=10.0
                )
                auth_data = orjson.loads(auth_msg)
                if (
                    auth_data.get("type") != "AUTH"
                    or auth_data.get("token") != expected_api_key
                ):
                    await websocket.send_text(
                        orjson.dumps({"type": "AUTH_FAILED"}).decode("utf-8")
                    )
                    await websocket.close(code=1008)
                    return
            except (asyncio.TimeoutError, Exception):
                await websocket.close(code=1008)
                return

    if script_name not in SAFE_SCRIPTS:
        await websocket.send_text(
            orjson.dumps({"type": "error", "line": "Invalid script name."}).decode(
                "utf-8"
            )
        )
        await websocket.close()
        return

    script_path = os.path.join("examples", script_name)
    if not os.path.exists(script_path):
        await websocket.send_text(
            orjson.dumps({"type": "error", "line": "Script file not found."}).decode(
                "utf-8"
            )
        )
        await websocket.close()
        return

    import sys

    # Use current running python executable
    python_bin = sys.executable

    env = os.environ.copy()
    env["PYTHONPATH"] = "."
    env["PYTHONUNBUFFERED"] = "1"
    env["MOCK_LLM"] = "true"  # Ensure it runs smoothly without raw API keys by default

    process = None
    try:
        process = await asyncio.create_subprocess_exec(
            python_bin,
            script_path,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
            env=env,
        )

        while True:
            line = await process.stdout.readline()
            if not line:
                break
            line_str = line.decode("utf-8", errors="replace").rstrip()
            await websocket.send_text(
                orjson.dumps({"type": "stdout", "line": line_str}).decode("utf-8")
            )

        await process.wait()
        exit_code = process.returncode
        await websocket.send_text(
            orjson.dumps({"type": "exit", "code": exit_code}).decode("utf-8")
        )
    except Exception as e:
        await websocket.send_text(
            orjson.dumps(
                {"type": "error", "line": f"Execution error: {str(e)}"}
            ).decode("utf-8")
        )
    finally:
        if process and process.returncode is None:
            try:
                process.terminate()
                await process.wait()
            except Exception as e:
                console.print(
                    f"[bold red]Error terminating script process:[/bold red] {e}"
                )
                pass
        try:
            await websocket.close()
        except Exception as e:
            console.print(f"[bold red]Error closing WebSocket:[/bold red] {e}")
            pass
