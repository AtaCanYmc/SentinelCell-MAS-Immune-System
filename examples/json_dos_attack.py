import asyncio
import os
import time
from rich.console import Console
from util import setup_mock_environment

setup_mock_environment()

console = Console()


async def simulate_json_dos():
    from src.core.orchestrator import SentinelOrchestrator
    from src.skills.validation import SemanticValidator
    from src.skills.repair import SelfHealingEngine
    from src.mcp_integration.client import SchemaRegistryClient

    os.environ["MAX_PAYLOAD_DEPTH"] = "15"
    os.environ["MAX_PAYLOAD_KEYS"] = "500"

    mcp = SchemaRegistryClient("src/mcp_integration/registry.py")
    validator = SemanticValidator(mcp)
    healer = SelfHealingEngine()
    orchestrator = SentinelOrchestrator(validator, healer)

    # 1. Depth Attack
    console.print("[bold yellow]--- Testing JSON Depth Attack ---[/bold yellow]")
    depth_payload = '{"a": ' * 20 + "1" + "}" * 20

    start_t = time.time()
    result = await orchestrator.intercept(
        "malicious_agent", "target_agent", depth_payload
    )
    end_t = time.time()

    if result is None:
        console.print(
            f"[bold green][+] System successfully dropped the depth attack in {end_t - start_t:.4f}s[/bold green]"
        )
    else:
        console.print("[bold red][!] System FAILED to drop the depth attack[/bold red]")

    # 2. Key Bombing Attack
    console.print(
        "\n[bold yellow]--- Testing JSON Key Bombing Attack ---[/bold yellow]"
    )
    key_bomb = "{" + ",".join([f'"key_{i}": 1' for i in range(1000)]) + "}"

    start_t = time.time()
    result2 = await orchestrator.intercept("malicious_agent", "target_agent", key_bomb)
    end_t = time.time()

    if result2 is None:
        console.print(
            f"[bold green][+] System successfully dropped the key bombing attack in {end_t - start_t:.4f}s[/bold green]"
        )
    else:
        console.print(
            "[bold red][!] System FAILED to drop the key bombing attack[/bold red]"
        )


if __name__ == "__main__":
    asyncio.run(simulate_json_dos())
