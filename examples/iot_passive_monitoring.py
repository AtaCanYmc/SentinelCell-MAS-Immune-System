import sys
import os
import asyncio
import json
import time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from src.core.orchestrator import SentinelOrchestrator
from src.skills.validation import SemanticValidator
from src.mcp_integration.client import SchemaRegistryClient
from src.skills.repair import SelfHealingEngine
from rich.console import Console
from util import setup_mock_environment

setup_mock_environment()

console = Console()


async def main():
    console.print("[bold cyan]=== IoT Passive Monitoring Simulation ===[/bold cyan]")

    # Enable passive monitoring explicitly
    os.environ["PASSIVE_MONITORING"] = "true"

    orchestrator = SentinelOrchestrator(
        validator=SemanticValidator(
            SchemaRegistryClient("src/mcp_integration/registry.py")
        ),
        healer=SelfHealingEngine(),
    )

    # Heavy broken payload
    iot_payload = {
        "sensor_id": "EDGE-1042",
        "temperature": "ERROR_NOT_A_NUMBER",
        "readings": [x for x in range(100)],
        "status": "online",
    }

    payload_str = json.dumps(iot_payload)

    console.print("\n[bold yellow][*] Edge Device sending payload...[/bold yellow]")
    start_time = time.time()

    # Will return immediately because of Passive Monitoring
    await orchestrator.intercept("edge_device_1", "telemetry_processor", payload_str)

    latency = (time.time() - start_time) * 1000
    console.print(
        f"\n[bold green][+] Traffic passed through transparently in {latency:.2f} ms![/bold green]"
    )
    console.print(
        "[dim]The heavy validation and healing are happening asynchronously in the background so the edge flow isn't blocked...[/dim]"
    )

    # Wait a bit to let the background task finish printing logs
    await asyncio.sleep(3)
    console.print("\n[bold cyan][*] Background task complete.[/bold cyan]")


if __name__ == "__main__":
    asyncio.run(main())
