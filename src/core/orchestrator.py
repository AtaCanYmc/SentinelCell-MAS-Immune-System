import json
from datetime import datetime
from typing import TypedDict
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

        # Decider Logic
        def decider_node(state: AgentState):
            if state.get("is_valid"):
                return "end"
            if state.get("repair_attempts", 0) >= 3:
                console.print(
                    "[bold red][!] Max repair attempts reached. Packet is unrecoverable.[/bold red]"
                )
                return "end"
            return "repair"

        graph.add_conditional_edges(
            "validate", decider_node, {"end": END, "repair": "repair"}
        )

        graph.add_edge("repair", "validate")
        self.workflow = graph.compile()

    async def intercept(
        self, agent_source: str, agent_target: str, payload: str
    ) -> dict | None:
        """
        Intercepts communication between agents near-instantly and runs the StateGraph.
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]

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
        }

        # Invoke the LangGraph workflow
        final_state = await self.workflow.ainvoke(initial_state)

        if final_state.get("is_valid"):
            if final_state.get("active_provider"):
                console.print(
                    f"[info][*] Healed using active provider: {final_state['active_provider']}[/info]"
                )
            console.print(
                "[success][+] PACKET VALID -> Allowing passthrough...[/success]"
            )
            return final_state["payload"]
        else:
            console.print("[danger][!] PACKET REJECTED -> Dropped.[/danger]")
            return None
