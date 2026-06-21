import asyncio
from rich.panel import Panel
from src.core.logger import get_console
from src.agents.validator_agent import SentinelCell

console = get_console()


async def run_dummy_traffic():
    console.print(
        Panel(
            "[bold bright_green]"
            "Initializing SentinelCell MAS Immune System (LangGraph Orchestrator)..."
            "[/bold bright_green]",
            border_style="green",
        )
    )

    sentinel = SentinelCell()

    await asyncio.sleep(1)
    console.print("\n[dim cyan]Injecting valid traffic...[/dim cyan]")
    await sentinel.intercept(
        "Agent_Alpha", "Agent_Beta", '{"message": "Hello Beta", "status": "ok"}'
    )

    await asyncio.sleep(0.5)
    console.print(
        "\n[bold yellow]Injecting semantically invalid traffic (missing message)...[/bold yellow]"
    )
    await sentinel.intercept("Agent_Gamma", "Agent_Beta", '{"status": "offline"}')

    await asyncio.sleep(0.5)
    console.print("\n[dim cyan]Injecting malformed JSON...[/dim cyan]")
    await sentinel.intercept(
        "Agent_Omega", "Agent_Zeta", '{"corrupted_data": "missing_keys",'
    )


async def main():
    await run_dummy_traffic()


if __name__ == "__main__":
    asyncio.run(main())
