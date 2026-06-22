import json
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
    last_memory_id: str | None


class SentinelOrchestrator:
    """
    Model Agnostic Orchestrator using LangGraph.
    """

    def __init__(self, validator, healer):
        self.validator = validator
        self.healer = healer

        # Build LangGraph
        graph = StateGraph(AgentState)

        graph.add_node("validate", self.validator.validate_node)
        graph.add_node("repair", self.healer.repair_node)

        graph.set_entry_point("validate")

        # VectorDB Logging Node
        async def log_to_vectordb_node(state: AgentState):
            if self.healer.memory and state.get("repair_attempts", 0) == 0:

                def _log_sync():
                    try:
                        import uuid
                        import time

                        doc_id = f"mem-valid-{uuid.uuid4()}"
                        memory_doc = (
                            f"Valid Payload: {json.dumps(state.get('payload', {}))}"
                        )
                        title = state.get("schema_dict", {}).get(
                            "title", "UnknownSchema"
                        )
                        self.healer.memory.add_memory(
                            doc_id=doc_id,
                            memory_doc=memory_doc,
                            metadata={
                                "schema": title,
                                "provider": "original",
                                "timestamp": time.time(),
                            },
                        )
                    except Exception:
                        pass

                import asyncio

                loop = asyncio.get_event_loop()
                loop.run_in_executor(None, _log_sync)
            return state

        graph.add_node("log_to_vectordb", log_to_vectordb_node)

        # Decider Logic
        def decider_node(state: AgentState):
            if state.get("is_valid"):
                return "log_to_vectordb"
            if state.get("repair_attempts", 0) >= 3:
                console.print(
                    "[bold red][!] Max repair attempts reached. Packet is unrecoverable.[/bold red]"
                )
                return "end"
            return "repair"

        graph.add_conditional_edges(
            "validate",
            decider_node,
            {"end": END, "repair": "repair", "log_to_vectordb": "log_to_vectordb"},
        )

        graph.add_edge("log_to_vectordb", END)
        graph.add_edge("repair", "validate")
        self.workflow = graph.compile()

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
            data = json.loads(payload)
        except json.JSONDecodeError as e:
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
            "last_memory_id": None,
        }

        # Invoke the LangGraph workflow
        final_state = await self.workflow.ainvoke(initial_state)

        # Record latency
        latency_seconds = time.time() - start_time
        metrics.latency.observe(latency_seconds)

        if final_state.get("is_valid"):
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
            if final_state.get("repair_attempts", 0) > 0:
                metrics.healing_failure.inc()
            metrics.payload_intercepts.labels(status="dropped").inc()
            console.print("[danger][!] PACKET REJECTED -> Dropped.[/danger]")
            self._log_to_dlq(
                agent_source,
                agent_target,
                json.dumps(final_state.get("payload", {})),
                "Unrecoverable Invalid Payload",
            )
            return None

    def _log_to_dlq(self, source: str, target: str, payload: str, reason: str):
        import time
        import os

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
                f.write(json.dumps(entry) + "\n")
        except Exception:
            pass
