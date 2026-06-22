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
        "[bold cyan]=== Semantic Drift (Chaos Test) Simulation ===[/bold cyan]"
    )

    # 1. Expected schema
    user_profile_schema = {
        "title": "UserProfile",
        "type": "object",
        "properties": {
            "first_name": {"type": "string"},
            "last_name": {"type": "string"},
            "email": {"type": "string"},
            "age": {"type": "integer"},
        },
        "required": ["first_name", "last_name", "email"],
    }

    from src.core.mcp_client import FastMCPClient
    from src.skills.validation import SchemaValidator
    from src.skills.repair import SelfHealingEngine

    validator = SchemaValidator(FastMCPClient())
    validator._cache["user_profile_agent"] = {
        "schema": user_profile_schema,
        "expires_at": 9999999999,
    }

    orchestrator = SentinelOrchestrator(validator=validator, healer=SelfHealingEngine())

    # A completely garbled payload where the original data means nothing
    # to the target schema, forcing the LLM to invent 100% of the payload.
    garbled_payload = {
        "random_key_1": "apple",
        "random_key_2": "banana",
        "nested": {"foo": "bar"},
    }

    console.print(
        "\n[bold yellow][*] Attacker sending completely unrelated (garbled) payload to UserProfile Agent...[/bold yellow]"
    )
    console.print(json.dumps(garbled_payload, indent=2))

    console.print(
        "\n[bold yellow][*] SentinelCell Intercepting and Healing...[/bold yellow]"
    )
    console.print(
        "[dim]The LLM will try to create a valid UserProfile schema, but it will have to invent the data, causing Semantic Drift.[/dim]"
    )

    result = await orchestrator.intercept(
        "chaos_agent", "user_profile_agent", json.dumps(garbled_payload)
    )

    if result:
        console.print(
            "\n[bold red][-] FAILURE: The system accepted a semantically drifted payload![/bold red]"
        )
        console.print(json.dumps(result, indent=2))
    else:
        console.print(
            "\n[bold green][+] SUCCESS: The Dual-Layer Semantic Drift Guard successfully rejected the hallucinated payload![/bold green]"
        )


if __name__ == "__main__":
    asyncio.run(main())
