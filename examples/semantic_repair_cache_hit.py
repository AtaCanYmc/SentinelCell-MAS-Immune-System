import asyncio
import time
from rich.console import Console

console = Console()


class MockMCPClient:
    async def fetch_schema(self, target: str):
        return {
            "title": "SemanticCacheTarget",
            "type": "object",
            "properties": {"data": {"type": "integer"}},
            "required": ["data"],
        }


async def simulate_semantic_cache_hit():
    from src.core.orchestrator import SentinelOrchestrator
    from src.skills.validation import SemanticValidator
    from src.skills.repair import SelfHealingEngine

    validator = SemanticValidator(MockMCPClient())
    healer = SelfHealingEngine()
    orchestrator = SentinelOrchestrator(validator, healer)

    console.print(
        "[bold yellow]--- Testing Semantic Repair Cache Hit ---[/bold yellow]"
    )

    payload = '{"data": "forty-two"}'

    console.print("\n[dim]Sending packet for the FIRST time (Slow LLM path)...[/dim]")
    start1 = time.time()
    await orchestrator.intercept("agent_a", "target", payload)
    t1 = time.time() - start1

    console.print(f"[bold red]First attempt latency: {t1:.4f}s[/bold red]")

    console.print(
        "\n[dim]Sending EXACT same payload SECOND time (Fast Cache path)...[/dim]"
    )
    start2 = time.time()
    await orchestrator.intercept("agent_b", "target", payload)
    t2 = time.time() - start2

    console.print(f"[bold green]Second attempt latency: {t2:.4f}s[/bold green]")

    if t2 < t1:
        console.print(
            f"[bold cyan][+] Cache bypass successful. Latency improvement: {t1 / t2:.1f}x[/bold cyan]"
        )


if __name__ == "__main__":
    asyncio.run(simulate_semantic_cache_hit())
