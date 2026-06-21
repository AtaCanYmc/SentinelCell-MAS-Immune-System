import asyncio
from src.core.logger import get_console
from src.core.orchestrator import TrafficSniffer
from src.agents.validator_agent import SentinelCell

console = get_console()


async def main():
    console.print("[hack]Initializing SentinelCell MAS Immune System...[/hack]")
    sentinel = SentinelCell()

    # The TrafficSniffer intercepts traffic and validates it via SentinelCell
    sniffer = TrafficSniffer(validation_callback=sentinel.process)

    # Mock interception scenarios
    await asyncio.sleep(1)
    console.print("\n[dim cyan]Injecting valid traffic...[/dim cyan]")
    await sniffer.intercept(
        "Agent_Alpha", "Agent_Beta", '{"message": "Hello Beta", "status": "ok"}'
    )
    # Inject semantically invalid traffic (missing message)
    console.print(
        "\n[bold yellow]Injecting semantically invalid traffic (missing message)...[/bold yellow]"
    )
    await sniffer.intercept("Agent_Gamma", "Agent_Beta", '{"status": "offline"}')

    await asyncio.sleep(0.5)
    console.print("\n[dim cyan]Injecting malformed JSON...[/dim cyan]")
    await sniffer.intercept(
        "Agent_Omega", "Agent_Zeta", '{"corrupted_data": "missing_keys",'
    )


if __name__ == "__main__":
    asyncio.run(main())
