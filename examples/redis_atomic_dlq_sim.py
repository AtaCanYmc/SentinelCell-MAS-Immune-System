import asyncio
import os
import redis.asyncio as redis
from rich.console import Console
from util import setup_mock_environment

setup_mock_environment()

console = Console()


class MockMCPClient:
    async def fetch_schema(self, target: str):
        return {
            "title": "DLQ_Target",
            "type": "object",
            "properties": {"field": {"type": "string"}},
            "required": ["field"],
        }


async def simulate_atomic_dlq():
    from src.core.orchestrator import SentinelOrchestrator
    from src.skills.validation import SemanticValidator
    from src.skills.repair import SelfHealingEngine

    # Use localhost redis for this simulation. Make sure Redis is running.
    os.environ["REDIS_URL"] = "redis://localhost:6379/0"

    r = redis.from_url(os.environ["REDIS_URL"])

    try:
        await r.ping()
    except Exception as e:
        console.print(
            f"[bold red]Simulation requires a running Redis instance at localhost:6379: {e}[/bold red]"
        )
        return

    # Clear previous test data
    await r.delete("sentinel.dlq")
    await r.delete("sentinel.dlq.processing")
    await r.delete("sentinel.in")

    validator = SemanticValidator(MockMCPClient())
    healer = SelfHealingEngine()

    # We will mock the LLM to completely fail (simulate outage) so the packet goes to DLQ
    class FailingLLM:
        async def ainvoke(self, prompt):
            raise Exception("LLM API Outage")

    from src.core.llm_factory import LLMFactory

    LLMFactory.get_llm = lambda provider: FailingLLM()

    orchestrator = SentinelOrchestrator(validator, healer)

    console.print(
        "[bold yellow]--- Testing True Atomic Redis DLQ (BRPOPLPUSH) ---[/bold yellow]"
    )

    # Send a malformed payload that will fail deterministic repair and hit the failing LLM
    payload = '{"field": 123}'

    console.print(
        "\n[dim]1. Injecting payload to orchestrator (simulating LLM failure)...[/dim]"
    )
    await orchestrator.intercept("dlq_test_agent", "target", payload)

    # Check if it arrived in Redis DLQ
    dlq_len = await r.llen("sentinel.dlq")
    if dlq_len > 0:
        console.print(
            f"[bold green][+] Payload successfully written to Redis DLQ! (sentinel.dlq length: {dlq_len})[/bold green]"
        )
    else:
        console.print("[bold red][!] Payload NOT written to Redis DLQ.[/bold red]")
        return

    # Now we start the DLQ worker in the background
    console.print("\n[dim]2. Starting Atomic DLQ Worker (BRPOPLPUSH)...[/dim]")
    from src.gateways.dlq_worker import process_dlq

    worker_task = asyncio.create_task(process_dlq())

    # Give the worker a moment to process
    await asyncio.sleep(2)

    # Check final queues
    dlq_len_after = await r.llen("sentinel.dlq")
    processing_len = await r.llen("sentinel.dlq.processing")
    sentinel_in_len = await r.llen("sentinel.in")

    console.print(f"-> sentinel.dlq length: {dlq_len_after}")
    console.print(
        f"-> sentinel.dlq.processing length: {processing_len} (Safe Commit Zone)"
    )
    console.print(f"-> sentinel.in length: {sentinel_in_len}")

    if sentinel_in_len > 0:
        item = await r.lpop("sentinel.in")
        console.print(
            "[bold green][+] Message completely migrated to main bus atomically![/bold green]"
        )
        console.print(f"[bold white]{item}[/bold white]")

    worker_task.cancel()


if __name__ == "__main__":
    asyncio.run(simulate_atomic_dlq())
