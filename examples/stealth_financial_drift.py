import asyncio
import json
from src.core.orchestrator import SentinelOrchestrator
from src.skills.validation import SemanticValidator
from src.skills.repair import SelfHealingEngine
from rich.console import Console


# Create a mock MCP client that returns a strict financial schema
class MockMCPClient:
    async def fetch_schema(self, target):
        return {
            "title": "PaymentTransaction",
            "type": "object",
            "properties": {
                "transaction_id": {"type": "string"},
                "amount": {"type": "number"},
                "currency": {"type": "string"},
            },
            "required": ["transaction_id", "amount", "currency"],
        }


async def run_stealth_drift_test():
    console = Console()
    console.print(
        "[bold yellow][*] Starting Stealth Financial Drift Test[/bold yellow]"
    )

    # Initialize SentinelCell
    validator = SemanticValidator(MockMCPClient())
    healer = SelfHealingEngine()
    orchestrator = SentinelOrchestrator(validator, healer)

    # Simulated malformed payload: amount is inside a string instead of number to trigger repair
    malformed_payload = json.dumps(
        {
            "transaction_id": "TXN-999",
            "amount": "15000",  # schema requires number, this triggers repair
            "currency": "USD",
        }
    )

    console.print(f"[dim]Sending Payload: {malformed_payload}[/dim]")

    # We will temporarily mock the LLM to return a "drifted" response
    from src.core.llm_factory import LLMFactory

    class MockLLM:
        async def ainvoke(self, prompt):
            class Response:
                content = (
                    '{"transaction_id": "TXN-999", "amount": 1500, "currency": "USD"}'
                )

            return Response()

    # Override the LLM factory
    original_get_llm = LLMFactory.get_llm
    LLMFactory.get_llm = lambda provider: MockLLM()

    try:
        console.print(
            "[cyan][*] LLM will attempt to 'heal' it but maliciously/accidentally changes 15000 to 1500...[/cyan]"
        )
        result = await orchestrator.intercept(
            "FinanceProducer", "LedgerConsumer", malformed_payload
        )

        if result is None:
            console.print(
                "[bold green][+] SUCCESS: Type-Aware Numeric Guard caught the financial drift and dropped the packet![/bold green]"
            )
        else:
            console.print(
                "[bold red][!] FAILURE: Semantic Guard failed! Drifted payload allowed through![/bold red]"
            )
    finally:
        LLMFactory.get_llm = original_get_llm


if __name__ == "__main__":
    asyncio.run(run_stealth_drift_test())
