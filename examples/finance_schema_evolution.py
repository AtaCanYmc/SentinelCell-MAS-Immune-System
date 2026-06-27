import sys
import os
import asyncio
import json

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from src.core.orchestrator import SentinelOrchestrator
from rich.console import Console

console = Console()


async def main():
    console.print(
        "[bold cyan]=== Finance MAS Schema Evolution Simulation ===[/bold cyan]"
    )

    # 1. Provide an expected schema (V1 format)
    v1_schema = {
        "title": "FinanceTransaction_v1",
        "type": "object",
        "properties": {
            "transaction_id": {"type": "string"},
            "amount": {"type": "number"},
            "currency": {
                "type": "string",
                "enum": ["TRY", "USD", "EUR"],
            },  # The consumer expects a simple string "TRY"
        },
        "required": ["transaction_id", "amount", "currency"],
    }

    # Register this v1 schema
    from src.mcp_integration.client import SchemaRegistryClient
    from src.skills.validation import SemanticValidator

    validator = SemanticValidator(
        SchemaRegistryClient("src/mcp_integration/registry.py")
    )
    validator._cache["fraud_agent"] = {"schema": v1_schema, "expires_at": 9999999999}

    from src.skills.repair import SelfHealingEngine

    orchestrator = SentinelOrchestrator(validator=validator, healer=SelfHealingEngine())

    # 2. Produce V2 Payload
    v2_payload = {
        "transaction_id": "TXN-987654",
        "amount": 50000.0,
        "currency": {
            "code": "TRY",
            "rate": 1.0,
        },  # V2 agent sends an object instead of string
    }

    console.print(
        "\n[bold yellow][*] V2 Producer Agent (Core Banking) sending payload to V1 Consumer Agent (Fraud Detection)...[/bold yellow]"
    )
    console.print(json.dumps(v2_payload, indent=2))

    console.print("\n[bold yellow][*] SentinelCell Intercepting...[/bold yellow]")
    result = await orchestrator.intercept(
        "core_banking_agent", "fraud_agent", json.dumps(v2_payload)
    )

    if result:
        console.print(
            "\n[bold green][+] Interception Complete! Repaired (Downgraded to V1) Payload Delivered to Consumer:[/bold green]"
        )
        console.print(result)
    else:
        console.print("\n[bold red][-] Payload was dropped.[/bold red]")


if __name__ == "__main__":
    asyncio.run(main())
