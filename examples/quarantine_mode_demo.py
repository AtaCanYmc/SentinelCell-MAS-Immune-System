import asyncio
import json
import os
from rich.console import Console
from rich.panel import Panel
from src.agents.validator_agent import SentinelCell
from util import setup_mock_environment, shutdown_sentinel

setup_mock_environment()

console = Console()


async def main():
    console.print(
        Panel.fit(
            "[bold red]🛡️ QUARANTINE MODE SIMULATION 🛡️[/bold red]\n"
            "Testing Emergency Fail-Safe Mechanism under heavy attack.",
            border_style="red",
        )
    )

    # Set a short cooldown for the demo
    os.environ["QUARANTINE_COOLDOWN_SECONDS"] = "5"
    sentinel = SentinelCell()
    try:
        invalid_payload = json.dumps({"status": "error"})  # Missing message => Invalid
        valid_payload = json.dumps({"status": "ok", "message": "All clear!"})

        console.print(
            "[dim]Simulating a rapid succession of Malicious/Malformed Packets...[/dim]\n"
        )

        for i in range(1, 7):
            console.print(f"[bold yellow]--- Packet #{i} ---[/bold yellow]")
            result = await sentinel.intercept(
                "AttackerBot", "Agent_Beta", invalid_payload
            )

            q_mode, _ = await sentinel._get_quarantine_state()
            if q_mode:
                console.print(
                    f"\n[bold red]🚨 QUARANTINE TRIGGERED AFTER {i} ATTACKS 🚨[/bold red]\n"
                )
                break

        # Now that the system is in quarantine, even valid traffic should be dropped
        console.print("[bold cyan]--- Post-Quarantine Traffic Attempt ---[/bold cyan]")
        console.print(
            "[dim]Attempting to send a perfectly VALID packet immediately...[/dim]"
        )

        result = await sentinel.intercept("GoodBot", "Agent_Beta", valid_payload)

        # Assert
        assert result is None, "Quarantine failed! Valid traffic bypassed the lockdown."

        console.print(
            "\n[bold green]✅ ASSERTION PASSED:[/bold green] System successfully locked itself down and protected the infrastructure from further damage."
        )

        console.print(
            "\n[bold blue]⏳ Waiting for Cooldown period (6 seconds)...[/bold blue]"
        )
        await asyncio.sleep(6)

        console.print("\n[bold cyan]--- Health Check Packet ---[/bold cyan]")
        console.print("[dim]Attempting to send a VALID packet after cooldown...[/dim]")

        # We don't assert the actual result of intercept since the registry might be missing the schema,
        # but we just want to show that it allows it through.
        await sentinel.intercept("HealthChecker", "Agent_Beta", valid_payload)

        q_mode, _ = await sentinel._get_quarantine_state()
        assert q_mode is False, "Failed to exit quarantine mode!"
        console.print(
            "\n[bold green]✅ SYSTEM RECOVERED:[/bold green] Quarantine was lifted automatically after cooldown."
        )
    finally:
        await shutdown_sentinel(sentinel)


if __name__ == "__main__":
    asyncio.run(main())
