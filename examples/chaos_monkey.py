import asyncio
import json
from rich.console import Console
from rich.panel import Panel
from src.agents.validator_agent import SentinelCell

console = Console()


async def chaos_monkey():
    console.print(
        Panel.fit(
            "[bold red]🐒 CHAOS MONKEY INITIATED 🐒[/bold red]\n"
            "[dim]Simulating catastrophic payload corruption across the Multi-Agent System...[/dim]",
            border_style="red",
        )
    )

    sentinel = SentinelCell()
    try:
        # Define a series of chaotic payloads targeting Agent_Beta (which expects {"status": str, "message": str})
        # We will test SentinelCell's ability to heal or drop them gracefully.
        chaotic_payloads = [
            {
                "type": "PERFECT",
                "payload": json.dumps({"status": "ok", "message": "All systems go."}),
            },
            {"type": "MISSING_FIELD", "payload": json.dumps({"status": "error"})},
            {
                "type": "TYPE_MISMATCH",
                "payload": json.dumps(
                    {"status": 200, "message": ["Array instead of string"]}
                ),
            },
            {
                "type": "TOTAL_JUNK",
                "payload": "This is just a raw string, not even JSON! Total chaos!",
            },
            {
                "type": "REPEATED_ERROR",
                "payload": json.dumps({"status": "warning"}),
            },  # Should trigger RAG memory!
        ]

        for i, attack in enumerate(chaotic_payloads, 1):
            console.print(
                f"\n[bold magenta]=== Chaos Attack {i}/5: {attack['type']} ===[/bold magenta]"
            )
            console.print(f"[dim]Injecting: {attack['payload']}[/dim]")

            # Simulate network latency
            await asyncio.sleep(1)

            result = await sentinel.intercept(
                source="Chaos_Monkey",
                target="Agent_Beta",
                payload=attack["payload"],
            )

            if result:
                console.print(
                    f"[bold green]🛡️ SYSTEM SECURED. Healed Payload: {result}[/bold green]"
                )
            else:
                console.print(
                    "[bold red]⛔ SYSTEM SECURED. Threat Dropped (Unrecoverable).[/bold red]"
                )

            await asyncio.sleep(2)

        console.print(
            Panel.fit(
                "[bold green]✅ CHAOS SIMULATION COMPLETE ✅[/bold green]\n"
                "[dim]SentinelCell successfully defended the MAS pipeline from catastrophic failures.[/dim]",
                border_style="green",
            )
        )
    finally:
        await sentinel.stop()


if __name__ == "__main__":
    asyncio.run(chaos_monkey())
