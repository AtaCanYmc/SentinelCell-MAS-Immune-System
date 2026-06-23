import os
import orjson
import asyncio
import dotenv
from pydantic import BaseModel
from fastapi import (
    FastAPI,
    Request,
    HTTPException,
    WebSocket,
    WebSocketDisconnect,
    Depends,
    Header,
)
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.staticfiles import StaticFiles
import redis.asyncio as redis
from src.agents.validator_agent import SentinelCell
from prometheus_client import make_asgi_app

app = FastAPI(
    title="SentinelCell Guardian Gateway",
    description="Transparent API Gateway and Live Dashboard for Multi-Agent Systems",
)
sentinel = SentinelCell()

security = HTTPBearer(auto_error=False)


def verify_api_key(credentials: HTTPAuthorizationCredentials = Depends(security)):
    expected_api_key = os.getenv("API_KEY_SECRET")
    if not expected_api_key:
        return True
    if not credentials or credentials.credentials != expected_api_key:
        raise HTTPException(status_code=401, detail="Invalid or missing API Key")
    return credentials.credentials


# Add Prometheus metrics route
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)


dashboard_dist_path = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "dashboard", "dist"
)

if os.path.exists(dashboard_dist_path):
    app.mount(
        "/assets",
        StaticFiles(directory=os.path.join(dashboard_dist_path, "assets")),
        name="assets",
    )


@app.get("/dashboard", response_class=HTMLResponse)
async def get_dashboard():
    """Serves the Vite React Live Hackerman Dashboard"""
    index_path = os.path.join(dashboard_dist_path, "index.html")
    if os.path.exists(index_path):
        with open(index_path, "r") as f:
            return f.read()

    # Fallback to legacy
    legacy_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)), "frontend", "dashboard.html"
    )
    try:
        with open(legacy_path, "r") as f:
            return f.read()
    except FileNotFoundError:
        return "<h1>Dashboard UI not found. Please run 'npm run build' in the dashboard/ folder.</h1>"


@app.websocket("/ws/logs")
async def websocket_logs(websocket: WebSocket):
    """Streams live SentinelCell logs from Redis PubSub to connected WebSockets"""
    await websocket.accept()
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
        except Exception:
            pass
    except Exception as e:
        try:
            await websocket.send_text(
                orjson.dumps({"type": "SYSTEM_ERROR", "content": str(e)}).decode(
                    "utf-8"
                )
            )
        except Exception:
            pass


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
                cached_response = await r.get(f"idempotency:{x_idempotency_key}")
                if cached_response:
                    return JSONResponse(
                        status_code=208, content=orjson.loads(cached_response)
                    )
            except Exception:
                pass

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
                    f"idempotency:{x_idempotency_key}",
                    86400,
                    orjson.dumps(result).decode("utf-8"),
                )
            except Exception:
                pass

        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/memory/purge")
async def purge_memory(days: int = 30, api_key: str = Depends(verify_api_key)):
    """
    Purges old hallucination corrections from the VectorDB
    to prevent memory bloat and maintain optimal RAG performance.
    """
    try:
        from src.core.memory_factory import MemoryFactory

        memory_store = MemoryFactory.get_memory_store()
        deleted_count = memory_store.purge_old_memories(days=days)
        return {
            "status": "success",
            "message": f"Purged memories older than {days} days.",
            "deleted_count": deleted_count,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


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
        raise HTTPException(status_code=500, detail=str(e))


class ConfigUpdate(BaseModel):
    PROVIDER_ORDER: str = None
    MAX_REPAIR_ATTEMPTS: str = None
    QUARANTINE_ERROR_THRESHOLD: str = None
    LLM_RATE_LIMIT_PER_MIN: str = None
    PASSIVE_MONITORING: str = None
    MCP_FAILURE_POLICY: str = None


@app.get("/api/config")
async def get_config(api_key: str = Depends(verify_api_key)):
    """Returns safe environment variables for the settings dashboard."""
    env_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))), ".env"
    )
    config = dotenv.dotenv_values(env_path)

    safe_keys = [
        "PROVIDER_ORDER",
        "MAX_REPAIR_ATTEMPTS",
        "QUARANTINE_ERROR_THRESHOLD",
        "LLM_RATE_LIMIT_PER_MIN",
        "PASSIVE_MONITORING",
        "MCP_FAILURE_POLICY",
    ]

    return {k: config.get(k, "") for k in safe_keys}


@app.post("/api/config")
async def update_config(config: ConfigUpdate, api_key: str = Depends(verify_api_key)):
    """Updates .env file with new configurations."""
    env_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))), ".env"
    )

    if not os.path.exists(env_path):
        open(env_path, "a").close()

    updated = {}
    for key, value in config.model_dump(exclude_unset=True).items():
        if value is not None:
            dotenv.set_key(env_path, key, str(value))
            updated[key] = value
            os.environ[key] = str(value)

    return {"status": "success", "updated": updated}


@app.get("/api/dlq")
async def get_dlq(api_key: str = Depends(verify_api_key)):
    """Returns the Dead Letter Queue logs for the Quarantine UI."""
    dlq_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
        ".antigravity",
        "logs",
        "dlq.json",
    )
    if not os.path.exists(dlq_path):
        return []

    logs = []
    with open(dlq_path, "r") as f:
        for line in f:
            if line.strip():
                try:
                    logs.append(orjson.loads(line))
                except orjson.JSONDecodeError:
                    pass
    # Return latest first
    return logs[::-1]


class ReplayRequest(BaseModel):
    source: str
    target: str
    payload: str


@app.post("/api/replay")
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
        raise HTTPException(status_code=500, detail=str(e))
