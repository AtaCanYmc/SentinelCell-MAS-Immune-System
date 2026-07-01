import os
import orjson
import asyncio
import time
import dotenv
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
from fastapi.responses import HTMLResponse, JSONResponse
from src.core.logger import get_console

from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.staticfiles import StaticFiles
import redis.asyncio as redis
from src.agents.validator_agent import SentinelCell
from prometheus_client import make_asgi_app
from src.core.session_manager import create_session_token, verify_session_token

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


dashboard_dist_path = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "dashboard", "dist"
)

assets_path = os.path.join(dashboard_dist_path, "assets")
if os.path.exists(assets_path):
    app.mount(
        "/assets",
        StaticFiles(directory=assets_path),
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
async def websocket_logs(websocket: WebSocket, token: str | None = None):
    """Streams live SentinelCell logs from Redis PubSub to connected WebSockets"""
    expected_api_key = os.getenv("API_KEY_SECRET")
    if expected_api_key:
        session_cookie = websocket.cookies.get("sentinel_session")
        has_valid_cookie = (
            session_cookie and verify_session_token(session_cookie) is not None
        )
        has_valid_token = token == expected_api_key
        if not has_valid_cookie and not has_valid_token:
            await websocket.accept()
            await websocket.close(code=4001)
            return

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
                cached_response = await r.get(f"idempotency:{x_idempotency_key}")
                if cached_response:
                    return JSONResponse(
                        status_code=208, content=orjson.loads(cached_response)
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
                    f"idempotency:{x_idempotency_key}",
                    86400,
                    orjson.dumps(result).decode("utf-8"),
                )
            except Exception as redis_set_err:
                console.print(
                    f"[bold yellow]Redis idempotency write error:[/bold yellow] {redis_set_err}"
                )

        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


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
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.websocket("/ws/chat")
async def websocket_chat(
    websocket: WebSocket,
    lang: str = "en",
    provider: str | None = None,
    token: str | None = None,
):
    """
    WebSocket endpoint for real-time LLM chat streaming.
    """
    expected_api_key = os.getenv("API_KEY_SECRET")
    if expected_api_key:
        session_cookie = websocket.cookies.get("sentinel_session")
        has_valid_cookie = (
            session_cookie and verify_session_token(session_cookie) is not None
        )
        has_valid_token = token == expected_api_key
        if not has_valid_cookie and not has_valid_token:
            await websocket.accept()
            await websocket.close(code=4001)
            return

    await websocket.accept()
    from src.core.llm_factory import LLMFactory
    from src.core.chat_tools import get_chat_tools
    from langchain_core.messages import (
        SystemMessage,
        HumanMessage,
        ToolMessage,
        AIMessage,
    )
    from src.core.prompt_manager import PromptManager

    if not provider:
        provider = os.getenv("PROVIDER_ORDER", "OPENAI").split(",")[0].strip()

    try:
        llm = LLMFactory.get_llm(provider)

        # Initialize and bind tools
        tools = get_chat_tools(sentinel)
        tools_map = {t.name: t for t in tools}
        llm_with_tools = llm.bind_tools(tools)

        # Initialize conversation history outside the loop
        system_prompt = PromptManager.render("assistant.jinja2", {"lang": lang})
        messages = [
            SystemMessage(content=system_prompt),
        ]

        while True:
            data = await websocket.receive_text()

            # Send initial metadata
            await websocket.send_text(
                orjson.dumps({"type": "start", "provider": provider}).decode("utf-8")
            )

            # Append new user message to history
            messages.append(HumanMessage(content=data))

            # Upfront Intent Classification Step using the base LLM (no tools)
            is_system_intent = False
            intent_prompt = PromptManager.render(
                "intent_classifier.jinja2", {"user_message": data}
            )
            try:
                intent_resp = await llm.ainvoke([HumanMessage(content=intent_prompt)])
                intent = intent_resp.content.strip().upper()
                is_system_intent = "SYSTEM" in intent
            except Exception:
                # Fallback to system mode just in case
                is_system_intent = True

            try:
                # Agentic loop to resolve tool calls
                while True:
                    # If it's not a system query, invoke the base LLM (no tools bound)
                    # to prevent the model from hallucinating/forcing tool calls
                    active_llm = llm_with_tools if is_system_intent else llm
                    response = await active_llm.ainvoke(messages)

                    if (
                        hasattr(response, "tool_calls")
                        and response.tool_calls
                        and is_system_intent
                    ):
                        messages.append(response)

                        for tool_call in response.tool_calls:
                            tool_name = tool_call["name"]
                            tool_args = tool_call["args"]
                            tool_id = tool_call["id"]

                            # Stream back intermediate status message to show progress
                            status_msg = f"\n[System: Calling tool {tool_name}...]\n"
                            await websocket.send_text(
                                orjson.dumps(
                                    {"type": "chunk", "content": status_msg}
                                ).decode("utf-8")
                            )

                            # Execute tool
                            tool_obj = tools_map.get(tool_name)
                            if tool_obj:
                                try:
                                    tool_result = await tool_obj.ainvoke(tool_args)
                                except Exception as e:
                                    tool_result = f"Error executing tool: {e}"
                            else:
                                tool_result = f"Tool '{tool_name}' not found."

                            messages.append(
                                ToolMessage(
                                    content=str(tool_result), tool_call_id=tool_id
                                )
                            )

                        # Loop again to feed tool results back to LLM
                        continue
                    else:
                        # Once all tools are resolved, stream final text response and capture it for history
                        final_response_content = ""
                        async for chunk in llm.astream(messages):
                            content = (
                                chunk.content
                                if hasattr(chunk, "content")
                                else str(chunk)
                            )
                            if content:
                                final_response_content += content
                                await websocket.send_text(
                                    orjson.dumps(
                                        {"type": "chunk", "content": content}
                                    ).decode("utf-8")
                                )
                        messages.append(AIMessage(content=final_response_content))
                        break

                await websocket.send_text(orjson.dumps({"type": "end"}).decode("utf-8"))
            except Exception as stream_err:
                await websocket.send_text(
                    orjson.dumps({"type": "error", "content": str(stream_err)}).decode(
                        "utf-8"
                    )
                )
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
        raise HTTPException(status_code=500, detail=str(e))


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
    threshold = int(os.getenv("CIRCUIT_BREAKER_THRESHOLD", "5"))
    breakers = sentinel.orchestrator.agent_circuit_breakers
    result = []
    for agent, errors in breakers.items():
        failures = (
            errors.get("failures", 0) if isinstance(errors, dict) else (errors or 0)
        )
        result.append(
            {
                "id": agent,
                "errors": errors,
                "status": "TRIPPED" if failures >= threshold else "HEALTHY",
                "threshold": threshold,
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
    except Exception:
        return {
            "llm_requests_current_min": 0,
            "llm_rate_limit": int(os.getenv("LLM_RATE_LIMIT_PER_MIN", "50")),
            "max_payload_size": int(os.getenv("MAX_PAYLOAD_SIZE", "102400")),
        }


@app.get("/api/audit-logs")
async def get_audit_logs(api_key: str = Depends(verify_api_key)):
    """Returns OTel formatted decisions from the repair logs."""
    log_path = os.path.join(os.getcwd(), ".antigravity", "logs", "agent_decisions.json")
    if not os.path.exists(log_path):
        return {"logs": []}

    try:
        with open(log_path, "r") as f:
            logs = orjson.loads(f.read())
        return {"logs": logs[::-1]}  # newest first
    except Exception:
        return {"logs": []}


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
        raise HTTPException(status_code=500, detail=str(e))


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
async def ws_run_example(
    websocket: WebSocket, script_name: str, token: str | None = None
):
    """Runs a simulation script and streams stdout/stderr back in real-time."""
    expected_api_key = os.getenv("API_KEY_SECRET")
    if expected_api_key:
        session_cookie = websocket.cookies.get("sentinel_session")
        has_valid_cookie = (
            session_cookie and verify_session_token(session_cookie) is not None
        )
        has_valid_token = token == expected_api_key
        if not has_valid_cookie and not has_valid_token:
            await websocket.accept()
            await websocket.close(code=4001)
            return

    await websocket.accept()

    safe_scripts = [
        "adaptive_unlearning_demo.py",
        "agent_trust_score_degradation.py",
        "auth_bypass_injection.py",
        "auto_schema_inference_sim.py",
        "base64_poison_pill.py",
        "basic_usage.py",
        "chaos_monkey.py",
        "circuit_breaker_recovery.py",
        "custom_skill_demo.py",
        "finance_schema_evolution.py",
        "financial_drift_anomaly_sim.py",
        "financial_transaction_replay.py",
        "fintech_transaction_flow.py",
        "high_concurrency_burst.py",
        "high_concurrency_stress_test.py",
        "human_in_the_loop_approval.py",
        "iot_passive_monitoring.py",
        "iot_telemetry_recovery.py",
        "json_dos_attack.py",
        "kafka_heavy_duty_sim.py",
        "latency_benchmark.py",
        "mq_simulation_demo.py",
        "mqtt_iot_sensor_sim.py",
        "multi_agent_flow.py",
        "multi_language_drift.py",
        "opentelemetry_tracing_sim.py",
        "outbox_backpressure_test.py",
        "poison_pill_demo.py",
        "quarantine_mode_demo.py",
        "rabbitmq_heavy_duty_sim.py",
        "redis_atomic_dlq_sim.py",
        "redis_outage_fallback.py",
        "repair_prompt_injection_test.py",
        "schema_cache_hit_demo.py",
        "schema_evolution_conflict.py",
        "security_injection_demo.py",
        "semantic_drift_test.py",
        "semantic_repair_cache_hit.py",
        "silent_business_logic_corruption.py",
        "stealth_financial_drift.py",
        "wallet_exhaustion_dos_sim.py",
    ]

    if script_name not in safe_scripts:
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
            except Exception:
                pass
        try:
            await websocket.close()
        except Exception:
            pass
