import asyncio
from rich.console import Console
from util import setup_mock_environment

setup_mock_environment()

console = Console()


class MockMCPClient:
    async def fetch_schema(self, target: str):
        return {
            "title": "DegradingTarget",
            "type": "object",
            "properties": {"field": {"type": "string"}},
            "required": ["field"],
        }


async def simulate_trust_degradation():
    from src.core.orchestrator import SentinelOrchestrator
    from src.skills.validation import SemanticValidator
    from src.skills.repair import SelfHealingEngine

    validator = SemanticValidator(MockMCPClient())
    healer = SelfHealingEngine()
    orchestrator = SentinelOrchestrator(validator, healer)

    console.print(
        "[bold yellow]--- Testing Agent Trust Score Degradation ---[/bold yellow]"
    )

    agent = "degrading_agent"
    valid_payload = '{"field": "data"}'
    repairable_payload = '{"field": 123}'  # Coerced by deterministic healer
    malicious_payload = '{"field": "eval(something)"}'  # Triggers SecuritySanitizer

    async def run_step(desc, payload):
        console.print(f"\n[dim]{desc}[/dim]")
        await orchestrator.intercept(agent, "target", payload)
        score = orchestrator.agent_trust_scores.get(agent, 100)
        console.print(
            f"-> Current Trust Score for {agent}: [bold cyan]{score}[/bold cyan]"
        )
        return score

    score = await run_step(
        "Step 1: Sending valid payload (should be 100)", valid_payload
    )
    score = await run_step(
        "Step 2: Sending repairable payload (-5 penalty)", repairable_payload
    )
    score = await run_step(
        "Step 3: Sending repairable payload again (-5 penalty)", repairable_payload
    )
    score = await run_step(
        "Step 4: Sending malicious payload (Security Breach! -50 penalty)",
        malicious_payload,
    )

    if (
        score < 30
    ):  # 100 - 5 - 5 - 50 = 40. Wait, one more penalty to hit < 30 threshold
        pass
    else:
        score = await run_step(
            "Step 5: Sending another malicious payload to hit quarantine threshold",
            malicious_payload,
        )

    console.print(
        "\n[dim]Step 6: Sending valid payload AFTER quarantine threshold reached...[/dim]"
    )
    res = await orchestrator.intercept(agent, "target", valid_payload)

    if res is None:
        console.print(
            "[bold green][+] System correctly blocked valid payload because agent is QUARANTINED.[/bold green]"
        )
    else:
        console.print("[bold red][!] System failed to quarantine agent.[/bold red]")


if __name__ == "__main__":
    asyncio.run(simulate_trust_degradation())
