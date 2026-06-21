import os
import json
import asyncio
from fastapi import FastAPI, Request, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
import redis.asyncio as redis
from src.agents.validator_agent import SentinelCell
from prometheus_client import make_asgi_app

app = FastAPI(
    title="SentinelCell Guardian Gateway",
    description="Transparent API Gateway and Live Dashboard for Multi-Agent Systems",
)
sentinel = SentinelCell()

# Add Prometheus metrics route
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)


@app.get("/dashboard", response_class=HTMLResponse)
async def get_dashboard():
    """Serves the Vanilla JS Live Hackerman Dashboard"""
    dashboard_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)), "frontend", "dashboard.html"
    )
    try:
        with open(dashboard_path, "r") as f:
            return f.read()
    except FileNotFoundError:
        return "<h1>Dashboard UI not found. Are you missing src/frontend/dashboard.html?</h1>"


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
                json.dumps({"type": "SYSTEM_ERROR", "content": str(e)})
            )
        except Exception:
            pass


@app.post("/intercept")
async def intercept_traffic(source: str, target: str, request: Request):
    """
    HTTP Endpoint acting as the Guardian Gateway.
    Legacy agents can POST their payloads here to be scrubbed by the Immune System.
    """
    try:
        raw_body = (await request.body()).decode("utf-8")
        result = await sentinel.intercept(
            source=source, target=target, payload=raw_body
        )

        if result is None:
            raise HTTPException(
                status_code=400,
                detail="Payload rejected or unrecoverable by SentinelCell.",
            )

        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/memory/purge")
async def purge_memory(days: int = 30):
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
async def refresh_schema(agent_target: str = None):
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
