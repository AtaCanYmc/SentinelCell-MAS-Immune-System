import asyncio
import json
from rich.console import Console
from src.agents.validator_agent import SentinelCell

console = Console()


async def main():
    console.print("[bold green]Starting SentinelCell Basic Usage Demo...[/bold green]")
    sentinel = SentinelCell()

    # Intentionally missing the 'message' field which is required by the Agent_Beta schema
    malformed_payload = json.dumps({"status": "ok"})

    console.print("[cyan][>] Injecting malformed payload into SentinelCell...[/cyan]")
    console.print(f"Original Payload: {malformed_payload}")

    # SentinelCell will validate against Agent_Beta's schema via MCP and self-heal it
    result = await sentinel.intercept(
        source="Agent_Alpha", target="Agent_Beta", payload=malformed_payload
    )

    console.print("\n[bold yellow][*] Final Processed Result:[/bold yellow]")
    if result:
        console.print(
            f"[bold green][+] Successfully Healed Payload:[/bold green] {result}"
        )
    else:
        console.print("[bold red][!] Packet dropped or unrecoverable.[/bold red]")


if __name__ == "__main__":
    asyncio.run(main())
