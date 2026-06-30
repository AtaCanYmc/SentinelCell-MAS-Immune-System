import asyncio
import json
from rich.console import Console
from rich.panel import Panel
from util import setup_mock_environment, shutdown_sentinel

setup_mock_environment()

console = Console()


async def run_auto_schema_simulation():
    console.print(
        Panel.fit(
            "[bold cyan]Auto-Schema Inference (Observation Mode) Simulation[/bold cyan]\n"
            "Testing if the system can learn from valid packets and create a schema."
        )
    )

    from src.agents.validator_agent import SentinelCell

    sentinel = SentinelCell()
    try:
        target_agent = "Agent_Gamma"

        # Send 5 valid packets to reach the OBSERVATION_THRESHOLD (5)
        valid_payload = {"temperature": 22.5, "sensor_id": "T1", "status": "active"}

        # Mock the LLM call to return a generated schema
        async def mock_generate(*args, **kwargs):
            return {
                "title": "Agent_Gamma Schema",
                "type": "object",
                "properties": {
                    "temperature": {"type": "number"},
                    "sensor_id": {"type": "string"},
                    "status": {"type": "string"},
                },
                "required": ["temperature", "sensor_id", "status"],
                "additionalProperties": False,
            }

        sentinel.validator.schema_inferencer._generate_schema_from_llm = mock_generate

        console.print(
            f"\n[yellow]Sending 5 identical packets to {target_agent} to trigger inference...[/yellow]"
        )

        for i in range(5):
            console.print(f"[dim]Sending Packet {i + 1}/5...[/dim]")
            await sentinel.intercept(
                source="SensorNetwork",
                target=target_agent,
                payload=json.dumps(valid_payload),
            )
            await asyncio.sleep(0.5)

        console.print(
            "\n[yellow]Waiting 5 seconds for background LLM inference and MCP Registration to complete...[/yellow]"
        )
        await asyncio.sleep(5)

        # Send a 6th packet that violates the newly inferred schema
        invalid_payload = {
            "temperature": "high",  # Expected number
            "sensor_id": "T1",
            "status": "active",
        }

        console.print(
            f"\n[red]Sending 6th packet with INVALID type to {target_agent}...[/red]"
        )
        result = await sentinel.intercept(
            source="SensorNetwork",
            target=target_agent,
            payload=json.dumps(invalid_payload),
        )

        if result and "temperature" in str(result):
            console.print(
                f"[bold green]SUCCESS: SentinelCell healed the payload based on inferred schema![/bold green] -> {result}"
            )
        elif not result:
            console.print(
                "[bold green]SUCCESS: SentinelCell rejected the payload based on inferred schema![/bold green]"
            )
        else:
            console.print(
                f"[bold red]FAILED: SentinelCell let the invalid payload pass![/bold red] -> {result}"
            )
    finally:
        await shutdown_sentinel(sentinel)


if __name__ == "__main__":
    # Ensure MCP uses Mock LLM if we don't have keys, or just let it use OpenAI if configured
    asyncio.run(run_auto_schema_simulation())
