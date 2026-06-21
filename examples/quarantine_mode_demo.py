import asyncio
import json
from rich.console import Console
from rich.panel import Panel
from src.agents.validator_agent import SentinelCell

console = Console()


async def main():
    console.print(
        Panel.fit(
            "[bold red]🛡️ QUARANTINE MODE SIMULATION 🛡️[/bold red]\n"
            "Testing Emergency Fail-Safe Mechanism under heavy attack.",
            border_style="red",
        )
    )

    sentinel = SentinelCell()

    invalid_payload = json.dumps({"status": "error"})  # Missing message => Invalid
    valid_payload = json.dumps({"status": "ok", "message": "All clear!"})

    console.print(
        "[dim]Simulating a rapid succession of Malicious/Malformed Packets...[/dim]\n"
    )

    for i in range(1, 7):
        console.print(f"[bold yellow]--- Packet #{i} ---[/bold yellow]")
        result = await sentinel.intercept("AttackerBot", "Agent_Beta", invalid_payload)

        if sentinel.quarantine_mode:
            console.print(
                f"\n[bold red]🚨 QUARANTINE TRIGGERED AFTER {i} ATTACKS 🚨[/bold red]\n"
            )
            break

    # Now that the system is in quarantine, even valid traffic should be dropped
    console.print("[bold cyan]--- Post-Quarantine Traffic Attempt ---[/bold cyan]")
    console.print("[dim]Attempting to send a perfectly VALID packet...[/dim]")

    result = await sentinel.intercept("GoodBot", "Agent_Beta", valid_payload)

    # Assert
    assert result is None, "Quarantine failed! Valid traffic bypassed the lockdown."

    console.print(
        "\n[bold green]✅ ASSERTION PASSED:[/bold green] System successfully locked itself down and protected the infrastructure from further damage."
    )


if __name__ == "__main__":
    asyncio.run(main())
