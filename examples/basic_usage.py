import asyncio
from rich.console import Console
from src.core.orchestrator import SentinelOrchestrator

console = Console()


async def main():
    console.print("[bold green]Starting SentinelCell Basic Usage Demo...[/bold green]")
    orchestrator = SentinelOrchestrator()
    graph = orchestrator.compile()

    # Intentionally missing the 'message' field which is required by the schema
    state = {
        "payload": {"status": "ok"},
        "schema_dict": {
            "type": "object",
            "properties": {"status": {"type": "string"}, "message": {"type": "string"}},
            "required": ["status", "message"],
        },
        "repair_attempts": 0,
        "error_context": "",
        "active_provider": "",
    }

    console.print("[cyan][>] Injecting malformed payload into SentinelCell...[/cyan]")
    console.print(f"Original Payload: {state['payload']}")

    result = await graph.ainvoke(state)

    console.print("\n[bold yellow][*] Final Processed State:[/bold yellow]")
    if "payload" in result and result.get("error_context") == "":
        console.print(
            f"[bold green][+] Successfully Healed Payload:[/bold green] {result['payload']}"
        )
        console.print(f"Active Provider Used: {result['active_provider']}")
    else:
        console.print("[bold red][!] Packet dropped or unrecoverable.[/bold red]")


if __name__ == "__main__":
    asyncio.run(main())
