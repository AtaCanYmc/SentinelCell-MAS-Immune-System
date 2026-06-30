import asyncio
from rich.console import Console
from langgraph.graph import StateGraph, END
from src.core.orchestrator import AgentState
from util import setup_mock_environment

setup_mock_environment()

console = Console()


async def sanitize_node(state: AgentState) -> dict:
    """
    A custom skill that sanitizes passwords before they leave the node.
    """
    console.print(
        "[bold yellow][CustomSkill] Running Data Sanitizer Node...[/bold yellow]"
    )

    payload = state.get("payload", {})
    if isinstance(payload, dict) and "password" in payload:
        payload["password"] = "******"
        console.print(
            "[bold green][CustomSkill] Password masked successfully.[/bold green]"
        )

    return {"payload": payload}


async def main():
    console.print("[bold cyan]--- Custom Skill Construction Demo ---[/bold cyan]")

    # 1. Define the LangGraph State Machine
    workflow = StateGraph(AgentState)

    # 2. Add the custom skill node
    workflow.add_node("sanitize", sanitize_node)

    # 3. Define the flow
    workflow.set_entry_point("sanitize")
    workflow.add_edge("sanitize", END)

    # 4. Compile the graph
    graph = workflow.compile()

    # 5. Inject a risky payload
    state = {
        "payload": {"username": "admin", "password": "supersecretpassword123!"},
        "schema_dict": {},
        "repair_attempts": 0,
        "error_context": "",
        "active_provider": "",
    }

    console.print(f"Original Payload: {state['payload']}")

    # Execute the workflow
    result = await graph.ainvoke(state)

    console.print(f"[bold cyan]Sanitized Payload: {result['payload']}[/bold cyan]")


if __name__ == "__main__":
    asyncio.run(main())
