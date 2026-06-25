import orjson
from datetime import datetime
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, END
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.theme import Theme


# Hackerman theme for rich
custom_theme = Theme(
    {
        "info": "dim cyan",
        "warning": "magenta",
        "danger": "bold red",
        "success": "bold green",
        "hack": "bold bright_green",
    }
)
console = Console(theme=custom_theme)


class AgentState(TypedDict):
    agent_target: str
    payload: dict
    schema_dict: dict | None
    error_context: str | None
    is_valid: bool
    active_provider: str | None
    repair_attempts: int
    deterministic_repair_attempts: int
    last_memory_id: str | None


class SentinelOrchestrator:
    """
    Model Agnostic Orchestrator using LangGraph.
    """

    def __init__(self, validator, healer):
        import os

        self.validator = validator
        self.healer = healer
        self.agent_circuit_breakers = {}
        self.breaker_threshold = int(os.getenv("CIRCUIT_BREAKER_THRESHOLD", "5"))

        from langgraph.checkpoint.memory import MemorySaver
        from src.skills.deterministic_healer import DeterministicHealer

        self.deterministic_healer = DeterministicHealer()

        # Build LangGraph
        graph = StateGraph(AgentState)
        self.checkpointer = MemorySaver()

        graph.add_node("validate", self.validator.validate_node)
        graph.add_node("deterministic_repair", self.deterministic_healer.repair_node)
        graph.add_node("repair", self.healer.repair_node)

        graph.set_entry_point("validate")

        # VectorDB Logging Node
        async def log_to_vectordb_node(state: AgentState):
            if (
                state.get("repair_attempts", 0) == 0
                and state.get("deterministic_repair_attempts", 0) == 0
            ):
                import time
                import uuid
                import os
                import redis.asyncio as redis

                try:
                    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
                    r = redis.from_url(redis_url)
                    doc_id = f"mem-valid-{uuid.uuid4()}"
                    memory_doc = f"Valid Payload: {orjson.dumps(state.get('payload', {})).decode('utf-8')}"
                    title = state.get("schema_dict", {}).get("title", "UnknownSchema")

                    # Outbox Pattern: Push to Redis instead of synchronous write
                    outbox_entry = {
                        "doc_id": doc_id,
                        "memory_doc": memory_doc,
                        "metadata": {
                            "schema": title,
                            "provider": "original",
                            "timestamp": time.time(),
                        },
                    }
                    await r.lpush(
                        "sentinel.outbox", orjson.dumps(outbox_entry).decode("utf-8")
                    )
                    # Eviction Policy: Keep max 10,000 items to prevent Backpressure OOM
                    await r.ltrim("sentinel.outbox", 0, 9999)
                except Exception as e:
                    console.print(f"[bold red]Outbox Error: {e}[/bold red]")
            return state

        graph.add_node("log_to_vectordb", log_to_vectordb_node)

        # Decider Logic
        def decider_node(state: AgentState):
            if state.get("is_valid"):
                return "log_to_vectordb"

            # Data Poisoning Prevention
            err_ctx = state.get("error_context", "")
            if err_ctx and "SECURITY_BREACH" in err_ctx:
                console.print(
                    "[bold red][!] SECURITY BREACH DETECTED. Dropping packet immediately. No repair allowed.[/bold red]"
                )
                return "end"

            from src.skills.validation import SecuritySanitizer

            security_error = SecuritySanitizer.check_payload(state.get("payload", {}))
            if security_error:
                console.print(
                    f"[bold red][!] HIDDEN DATA POISONING DETECTED: {security_error}. Dropping packet.[/bold red]"
                )
                return "end"

            import os

            if state.get("deterministic_repair_attempts", 0) == 0:
                return "deterministic_repair"

            max_repair_attempts = int(os.getenv("MAX_REPAIR_ATTEMPTS", "3"))
            if state.get("repair_attempts", 0) >= max_repair_attempts:
                console.print(
                    f"[bold red][!] Max repair attempts reached ({max_repair_attempts}). Packet is unrecoverable.[/bold red]"
                )
                return "end"
            return "repair"

        graph.add_conditional_edges(
            "validate",
            decider_node,
            {
                "end": END,
                "deterministic_repair": "deterministic_repair",
                "repair": "repair",
                "log_to_vectordb": "log_to_vectordb",
            },
        )

        graph.add_edge("log_to_vectordb", END)
        graph.add_edge("deterministic_repair", "validate")
        graph.add_edge("repair", "validate")
        self.workflow = graph.compile(checkpointer=self.checkpointer)

    async def intercept(
        self, agent_source: str, agent_target: str, payload: str
    ) -> dict | None:
        """
        Intercepts communication between agents near-instantly and runs the StateGraph.
        """
        import time
        from src.core.telemetry import metrics

        start_time = time.time()

        # Log Intercept
        metrics.payload_intercepts.labels(status="received").inc()

        # Dynamic Circuit Breaker Check
        cb_state = self.agent_circuit_breakers.get(
            agent_source, {"failures": 0, "last_failure_time": 0}
        )
        if isinstance(cb_state, int):  # Migrate old int state if any
            cb_state = {"failures": cb_state, "last_failure_time": time.time()}

        if cb_state["failures"] >= getattr(self, "breaker_threshold", 5):
            import os

            cooldown = int(os.getenv("CIRCUIT_BREAKER_COOLDOWN", "60"))
            if time.time() - cb_state["last_failure_time"] > cooldown:
                console.print(
                    f"[bold yellow][!] CIRCUIT BREAKER HALF-OPEN for {agent_source}. Testing recovery...[/bold yellow]"
                )
            else:
                console.print(
                    f"[bold red][!] DYNAMIC CIRCUIT BREAKER TRIPPED for {agent_source}. Dropping traffic instantly.[/bold red]"
                )
                return None

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]

        import os

        max_payload_size = int(os.getenv("MAX_PAYLOAD_SIZE", "10000"))
        if len(payload) > max_payload_size:
            console.print(
                f"[bold red][!] Payload exceeds MAX_PAYLOAD_SIZE ({len(payload)} > {max_payload_size}). Dropping.[/bold red]"
            )
            self._log_to_dlq(agent_source, agent_target, payload, "Payload Too Large")
            return None

        # Log Interception (Hackerman style)
        panel_text = Text(
            f"[{timestamp}] INTERCEPTING TRAFFIC\n[>] Source: {agent_source}\n[>] Target: {agent_target}",
            style="hack",
        )
        console.print(
            Panel(
                panel_text,
                title="[SentinelCell] :: Sniffer Active",
                border_style="cyan",
            )
        )

        try:
            data = orjson.loads(payload)
        except orjson.JSONDecodeError as e:
            console.print(f"[danger][!] CRITICAL MALFORMED JSON DETECTED:[/danger] {e}")
            console.print("[warning][~] Routing to Self-Healing Engine...[/warning]")
            # Pass as generic dict so it can be healed
            data = {"_raw_unparsed_payload": payload}

        initial_state = {
            "agent_target": agent_target,
            "payload": data,
            "schema_dict": None,
            "error_context": "Invalid JSON format"
            if "_raw_unparsed_payload" in data
            else None,
            "is_valid": False,
            "active_provider": None,
            "repair_attempts": 0,
            "deterministic_repair_attempts": 0,
            "last_memory_id": None,
        }

        import os
        import asyncio

        # Data Poisoning Prevention: Do not repair SECURITY_BREACH
        # This will be handled inside the decider node to bypass repair.
        # Let's adjust decider_node to drop it instead. Wait, it's easier to check here.

        passive_mode = os.getenv("PASSIVE_MONITORING", "false").lower() == "true"
        import uuid

        thread_id = str(uuid.uuid4())
        config = {"configurable": {"thread_id": thread_id}}

        async def _run_workflow():
            final_state = await self.workflow.ainvoke(initial_state, config)
            latency_seconds = time.time() - start_time
            metrics.latency.observe(latency_seconds)

            if final_state.get("is_valid"):
                if agent_source in self.agent_circuit_breakers:
                    self.agent_circuit_breakers[agent_source] = {
                        "failures": 0,
                        "last_failure_time": 0,
                    }
                if final_state.get("repair_attempts", 0) > 0:
                    metrics.healing_success.inc()
                if final_state.get("active_provider"):
                    console.print(
                        f"[info][*] Healed using active provider: {final_state['active_provider']}[/info]"
                    )
                console.print(
                    "[success][+] PACKET VALID -> Allowing passthrough...[/success]"
                )
                return final_state["payload"]
            else:
                cb_state = self.agent_circuit_breakers.get(
                    agent_source, {"failures": 0, "last_failure_time": 0}
                )
                if isinstance(cb_state, int):
                    cb_state = {"failures": cb_state, "last_failure_time": time.time()}
                cb_state["failures"] += 1
                cb_state["last_failure_time"] = time.time()
                self.agent_circuit_breakers[agent_source] = cb_state

                if cb_state["failures"] >= getattr(self, "breaker_threshold", 5):
                    console.print(
                        f"[bold red][!] CIRCUIT BREAKER: {agent_source} has reached {cb_state['failures']} consecutive failures. Tripping breaker![/bold red]"
                    )

                if final_state.get("repair_attempts", 0) > 0:
                    metrics.healing_failure.inc()
                metrics.payload_intercepts.labels(status="dropped").inc()
                console.print("[danger][!] PACKET REJECTED -> Dropped.[/danger]")
                self._log_to_dlq(
                    agent_source,
                    agent_target,
                    orjson.dumps(final_state.get("payload", {})).decode("utf-8"),
                    "Unrecoverable Invalid Payload",
                )
                return None

        if passive_mode:
            # Passive monitoring: spawn task and return original payload immediately
            asyncio.create_task(_run_workflow())
            return payload
        else:
            return await _run_workflow()

    def _log_to_dlq(self, source: str, target: str, payload: str, reason: str):
        import time
        import os
        import asyncio

        dlq_dir = os.path.join(os.getcwd(), ".antigravity", "logs")
        os.makedirs(dlq_dir, exist_ok=True)
        dlq_path = os.path.join(dlq_dir, "dlq.json")

        entry = {
            "timestamp": time.time(),
            "source": source,
            "target": target,
            "reason": reason,
            "payload": payload,
        }
        try:
            with open(dlq_path, "a") as f:
                f.write(orjson.dumps(entry).decode("utf-8") + "\n")
        except Exception:
            pass

        # ChatOps Alerting
        webhook_url = os.getenv("SLACK_WEBHOOK_URL") or os.getenv("DISCORD_WEBHOOK_URL")
        if webhook_url:
            asyncio.create_task(
                self._send_webhook_alert(webhook_url, source, target, reason)
            )

    async def _send_webhook_alert(self, url, source, target, reason):
        try:
            import httpx

            message = {
                "text": f"🚨 *SentinelCell Alert* 🚨\n*Source:* {source}\n*Target:* {target}\n*Reason:* {reason}\n_Payload moved to DLQ_"
            }
            async with httpx.AsyncClient() as client:
                await client.post(url, json=message)
        except Exception as e:
            console.print(f"[dim yellow]Webhook delivery failed: {e}[/dim yellow]")
