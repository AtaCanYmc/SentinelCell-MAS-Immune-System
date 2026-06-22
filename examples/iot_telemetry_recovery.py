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
        "[bold cyan]=== IoT & Edge Device Telemetry Recovery Simulation ===[/bold cyan]"
    )

    # 1. Provide an expected schema
    iot_schema = {
        "title": "IoT_Telemetry_v1",
        "type": "object",
        "properties": {
            "device_id": {"type": "string"},
            "temperature": {"type": "number"},
            "humidity": {"type": "number"},
            "status": {"type": "string"},
        },
        "required": ["device_id", "temperature", "status"],
    }

    # Register this schema
    from src.core.mcp_client import FastMCPClient
    from src.skills.validation import SchemaValidator

    validator = SchemaValidator(FastMCPClient())
    validator._cache["data_lake"] = {"schema": iot_schema, "expires_at": 9999999999}

    orchestrator = SentinelOrchestrator(validator=validator, healer=None)
    # Re-import properly because orchestrator init defaults are complex
    from src.skills.repair import SelfHealingEngine

    orchestrator = SentinelOrchestrator(validator=validator, healer=SelfHealingEngine())

    # Simulating a broken JSON stream due to bad network
    broken_payload = """
    {
        "device_id": "ESP8266-A4",
        "temperature": 24.5,
        "humidity": 60,
        "status": "active"
    """  # Missing closing brace

    console.print(
        "\n[bold yellow][*] Edge Device sending broken JSON payload (Network Dropout)...[/bold yellow]"
    )
    console.print(broken_payload)

    console.print(
        "\n[bold yellow][*] SentinelCell Intercepting and Healing...[/bold yellow]"
    )
    result = await orchestrator.intercept("edge_sensor", "data_lake", broken_payload)

    if result:
        console.print(
            "\n[bold green][+] Interception Complete! Repaired Payload Delivered to Consumer:[/bold green]"
        )
        console.print(json.dumps(result, indent=2))
    else:
        console.print("\n[bold red][-] Payload was dropped.[/bold red]")


if __name__ == "__main__":
    asyncio.run(main())
