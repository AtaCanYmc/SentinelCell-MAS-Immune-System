import asyncio
from src.core.orchestrator import SentinelOrchestrator
from src.mcp_integration.client import SchemaRegistryClient
from src.skills.validation import SemanticValidator
from src.skills.repair import SelfHealingEngine
from rich.console import Console

console = Console()


async def main():
    validator = SemanticValidator(
        SchemaRegistryClient("src/mcp_integration/registry.py")
    )
    healer = SelfHealingEngine()
    orchestrator = SentinelOrchestrator(validator=validator, healer=healer)

    # Register a strict schema without additionalProperties
    await validator.mcp_client.register_schema(
        "AuthService",
        {
            "title": "AuthToken",
            "type": "object",
            "properties": {
                "user_id": {"type": "string"},
                "session_token": {"type": "string"},
            },
            "required": ["user_id", "session_token"],
            "additionalProperties": False,
        },
    )

    malicious_payload = '{"user_id": "123", "session_token": "abc", "isAdmin": true, "role": "superuser"}'

    console.print(
        "[bold yellow][*] Sending Malicious Payload (Privilege Escalation Injection)[/bold yellow]"
    )
    console.print(malicious_payload)

    result = await orchestrator.intercept(
        "AttackerAgent", "AuthService", malicious_payload
    )

    if result:
        console.print("[bold green][+] Payload scrubbed and accepted![/bold green]")
        console.print(result)
    else:
        console.print("[bold red][!] Payload rejected completely![/bold red]")


if __name__ == "__main__":
    asyncio.run(main())
