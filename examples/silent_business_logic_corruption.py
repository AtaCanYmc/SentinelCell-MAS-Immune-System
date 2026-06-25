import asyncio
from rich.console import Console

console = Console()


class MockMCPClient:
    async def fetch_schema(self, target: str):
        return {
            "title": "FinanceTarget",
            "type": "object",
            "properties": {
                "transaction_id": {"type": "string"},
                "amount": {"type": "integer"},
            },
            "required": ["transaction_id", "amount"],
        }


async def simulate_silent_corruption():
    from src.core.orchestrator import SentinelOrchestrator
    from src.skills.validation import SemanticValidator
    from src.skills.repair import SelfHealingEngine

    validator = SemanticValidator(MockMCPClient())
    healer = SelfHealingEngine()

    # We will mock the LLM to return a hallucinated value to simulate silent business logic corruption
    class HallucinatingLLM:
        async def ainvoke(self, prompt):
            class Response:
                content = '{"transaction_id": "T-123", "amount": 999}'

            return Response()

    # Monkey-patch the LLM Factory inside the healer
    from src.core.llm_factory import LLMFactory

    LLMFactory.get_llm = lambda provider: HallucinatingLLM()

    orchestrator = SentinelOrchestrator(validator, healer)

    console.print(
        "[bold yellow]--- Testing Silent Business Logic Corruption Guard ---[/bold yellow]"
    )

    # Original payload has amount 500, but has a trailing comma syntax error
    payload = '{"transaction_id": "T-123", "amount": 500,}'

    console.print(f"[dim]Sending malformed payload with amount=500: {payload}[/dim]")

    try:
        # Expected: The semantic drift guard in repair.py should catch the value change from 500 -> 999
        await orchestrator.intercept("agent_x", "target", payload)
    except Exception as e:
        console.print(f"[bold green][+] Corruption Caught! Exception: {e}[/bold green]")


if __name__ == "__main__":
    asyncio.run(simulate_silent_corruption())
