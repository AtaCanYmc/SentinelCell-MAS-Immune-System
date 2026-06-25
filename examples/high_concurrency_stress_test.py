import asyncio
import os
import time
from rich.console import Console

console = Console()


class MockMCPClient:
    async def fetch_schema(self, target: str):
        return {
            "title": "StressTarget",
            "type": "object",
            "properties": {"id": {"type": "integer"}},
        }


async def simulate_stress():
    from src.core.orchestrator import SentinelOrchestrator
    from src.skills.validation import SemanticValidator
    from src.skills.repair import SelfHealingEngine

    validator = SemanticValidator(MockMCPClient())
    healer = SelfHealingEngine()
    orchestrator = SentinelOrchestrator(validator, healer)

    console.print("[bold yellow]--- Testing High Concurrency Stress ---[/bold yellow]")

    payload = '{"id": 123}'

    async def fire_request(i):
        # We will use valid payloads to flood the system and outbox
        await orchestrator.intercept(f"agent_{i}", "target", payload)

    concurrency = 500
    console.print(f"[dim]Firing {concurrency} requests concurrently...[/dim]")

    start_t = time.time()
    await asyncio.gather(*(fire_request(i) for i in range(concurrency)))
    end_t = time.time()

    console.print(
        f"[bold green][+] Processed {concurrency} requests in {end_t - start_t:.4f}s[/bold green]"
    )
    console.print(
        f"[bold cyan]Throughput: {concurrency / (end_t - start_t):.2f} req/sec[/bold cyan]"
    )


if __name__ == "__main__":
    # Disable rich console logs from orchestrator to avoid terminal spam during stress test
    os.environ["PYTHONASYNCIODEBUG"] = "0"
    asyncio.run(simulate_stress())
