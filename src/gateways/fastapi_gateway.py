import os
import asyncio
import orjson
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from prometheus_client import make_asgi_app

from src.core.logger import get_console
from src.gateways.config_validator import validate_startup_config
from src.gateways.shared import sentinel

# Include Sub-Routers
from src.gateways.routers.auth import router as auth_router
from src.gateways.routers.intercept import router as intercept_router
from src.gateways.routers.agents import router as agents_router
from src.gateways.routers.observability import router as observability_router
from src.gateways.routers.chat import router as chat_router
from src.gateways.routers.hitl import router as hitl_router
from src.gateways.routers.examples import router as examples_router

# Run Startup Config Validation
validate_startup_config()

console = get_console()


async def metrics_broadcaster_task():
    import redis.asyncio as redis
    from src.gateways.routers.observability import _fetch_metrics_data

    while True:
        try:
            metrics_data = await _fetch_metrics_data()
            payload = {
                "type": "METRICS",
                "content": orjson.dumps(metrics_data).decode("utf-8"),
            }
            redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
            r = redis.from_url(redis_url)
            await r.publish("sentinel.logs", orjson.dumps(payload).decode("utf-8"))
            await r.aclose()
        except Exception as e:
            console.print(f"[bold red]Metrics broadcaster task error:[/bold red] {e}")
        await asyncio.sleep(3.0)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    try:
        await sentinel.mcp_client.start()
    except Exception as e:
        console.print(
            f"[bold red]Failed to start persistent MCP client: {e}[/bold red]"
        )
    app.state.metrics_task = asyncio.create_task(metrics_broadcaster_task())
    yield
    # Shutdown
    if hasattr(app.state, "metrics_task"):
        app.state.metrics_task.cancel()
        try:
            await app.state.metrics_task
        except asyncio.CancelledError:
            pass
    try:
        await sentinel.stop()
    except Exception as e:
        console.print(f"[bold red]Failed to stop persistent MCP client: {e}[/bold red]")


app = FastAPI(
    title="SentinelCell Guardian Gateway",
    description="Transparent API Gateway and Live Dashboard for Multi-Agent Systems",
    lifespan=lifespan,
)


# Anti-CSRF Protection Middleware (Double-Submit Cookie Pattern)
@app.middleware("http")
async def csrf_middleware(request, call_next):
    if request.method in ("POST", "PUT", "DELETE", "PATCH"):
        path = request.url.path
        # Enforce check on dashboard API endpoints, excluding login
        if path.startswith("/api/") and not path.startswith("/api/auth/login"):
            cookie_csrf = request.cookies.get("sentinel_csrf")
            header_csrf = request.headers.get("X-CSRF-Token")

            if not cookie_csrf or not header_csrf or cookie_csrf != header_csrf:
                return JSONResponse(
                    status_code=403,
                    content={"status": "error", "message": "CSRF verification failed"},
                )
    return await call_next(request)


# Add Prometheus metrics route
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)


@app.get("/dashboard")
async def dashboard_ui():
    """Lightweight health/placeholder route so the test-suite and simple
    deployments can probe the dashboard entrypoint. The real dashboard is
    served by the separate frontend container in production setups.
    """
    return JSONResponse(content={"status": "ok", "page": "dashboard"})


app.include_router(auth_router)
app.include_router(intercept_router)
app.include_router(agents_router)
app.include_router(observability_router)
app.include_router(chat_router)
app.include_router(hitl_router)
app.include_router(examples_router)
