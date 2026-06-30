import os
import json
import asyncio
from rich.console import Console
from rich.panel import Panel
from src.antigravity.integrity import verify_chain

console = Console()


async def demo_integrity():
    console.print(
        Panel.fit("[bold cyan]🛡️ Antigravity Cryptographic Integrity Demo 🛡️[/bold cyan]")
    )

    log_dir = os.path.join(os.getcwd(), ".antigravity", "logs")
    os.makedirs(log_dir, exist_ok=True)
    log_path = os.path.join(log_dir, "agent_decisions.json")

    # 1. Create Mock Decisions
    console.print(
        "\n[yellow][*] Step 1: Simulating Agent Decisions and Logging...[/yellow]"
    )
    mock_logs = [
        {
            "timestamp": 1690000000,
            "action": "intercept",
            "source": "AgentA",
            "target": "AgentB",
            "decision": "heal",
        },
        {
            "timestamp": 1690000100,
            "action": "intercept",
            "source": "Hacker",
            "target": "DB",
            "decision": "drop",
        },
        {
            "timestamp": 1690000200,
            "action": "intercept",
            "source": "AgentB",
            "target": "AgentC",
            "decision": "pass",
        },
    ]

    with open(log_path, "w") as f:
        json.dump(mock_logs, f, indent=2)

    # 2. Verify Valid Chain
    console.print(
        "\n[yellow][*] Step 2: Running Cryptographic Verification on Valid Logs...[/yellow]"
    )
    verify_chain()

    # 3. Simulate Attacker Tampering
    console.print(
        "\n[red][!] Step 3: Simulating Malicious Tampering (Modifying History)...[/red]"
    )
    console.print("[dim]Attacker changes 'drop' to 'pass' to hide their tracks.[/dim]")

    mock_logs[1]["decision"] = "pass"  # Malicious change

    with open(log_path, "w") as f:
        json.dump(mock_logs, f, indent=2)

    # 4. Verify Corrupted Chain
    console.print(
        "\n[yellow][*] Step 4: Running Verification on Tampered Logs...[/yellow]"
    )
    # We will capture the output mentally, but verify_chain() prints it.
    verify_chain()

    console.print(
        "\n[bold green]✅ Demo Complete! SentinelCell detects tampering instantly.[/bold green]"
    )

    # Cleanup
    if os.path.exists(log_path):
        os.remove(log_path)


if __name__ == "__main__":
    asyncio.run(demo_integrity())
