import sys
import os
import asyncio
import json

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from src.core.orchestrator import SentinelOrchestrator
from rich.console import Console

console = Console()


async def main():
    console.print("[bold cyan]=== FinTech Transaction Flow Simulation ===[/bold cyan]")

    # 1. Provide an expected schema
    fintech_schema = {
        "title": "WireTransfer_v1",
        "type": "object",
        "properties": {
            "sender_account": {"type": "string"},
            "receiver_account": {"type": "string"},
            "currency": {"type": "string"},
            "amount": {"type": "number"},
        },
        "required": ["sender_account", "receiver_account", "amount", "currency"],
    }

    from src.core.mcp_client import FastMCPClient
    from src.skills.validation import SchemaValidator
    from src.skills.repair import SelfHealingEngine

    validator = SchemaValidator(FastMCPClient())
    validator._cache["core_ledger"] = {
        "schema": fintech_schema,
        "expires_at": 9999999999,
    }

    orchestrator = SentinelOrchestrator(validator=validator, healer=SelfHealingEngine())

    # Financial payload missing a critical field (e.g. amount)
    fintech_payload = {
        "sender_account": "TR123456789",
        "receiver_account": "US987654321",
        "currency": "USD",
        # "amount": 150000.00 is missing!
    }

    console.print(
        "\n[bold yellow][*] Payment Gateway sending payload with MISSING 'amount'...[/bold yellow]"
    )
    console.print(json.dumps(fintech_payload, indent=2))

    console.print("\n[bold yellow][*] SentinelCell Intercepting...[/bold yellow]")
    console.print(
        "[dim]The LLM will try to invent an amount. The Semantic Drift Guard will check if it's safe.[/dim]"
    )
    result = await orchestrator.intercept(
        "payment_gateway", "core_ledger", json.dumps(fintech_payload)
    )

    if result:
        console.print(
            "\n[bold green][+] Interception Complete! Repaired Payload Delivered to Consumer:[/bold green]"
        )
        console.print(json.dumps(result, indent=2))
    else:
        console.print(
            "\n[bold red][-] Payload was dropped (Quarantined/Rejected).[/bold red]"
        )


if __name__ == "__main__":
    asyncio.run(main())
