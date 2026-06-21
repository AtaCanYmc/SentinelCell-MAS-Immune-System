import asyncio
import json
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.theme import Theme
from datetime import datetime
from typing import Callable, Awaitable, Any

# Hackerman theme for rich
custom_theme = Theme(
    {
        "info": "dim cyan",
        "warning": "magenta",
        "danger": "bold red",
        "success": "bold green",
        "hack": "bold bright_green",
    }
)
console = Console(theme=custom_theme)


class TrafficSniffer:
    """
    Asynchronous Interceptor for Multi-Agent Systems.
    Captures JSON data flows non-intrusively.
    """

    def __init__(
        self, validation_callback: Callable[[str, dict], Awaitable[bool]] = None
    ):
        self.validation_callback = validation_callback

    async def intercept(
        self, agent_source: str, agent_target: str, payload: str
    ) -> Any:
        """
        Intercepts communication between agents near-instantly.
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]

        # Log Interception (Hackerman style)
        panel_text = Text(
            f"[{timestamp}] INTERCEPTING TRAFFIC\n[>] Source: {agent_source}\n[>] Target: {agent_target}",
            style="hack",
        )
        console.print(
            Panel(
                panel_text,
                title="[SentinelCell] :: Sniffer Active",
                border_style="cyan",
            )
        )

        # Non-intrusive async parse
        try:
            data = json.loads(payload)
        except json.JSONDecodeError as e:
            console.print(f"[danger][!] CRITICAL MALFORMED JSON DETECTED:[/danger] {e}")
            # Here we would normally route to Healing Protocol instead of dropping
            console.print("[warning][~] Routing to Self-Healing Engine...[/warning]")
            return None

        if self.validation_callback:
            console.print("[info][*] Passing packet to Semantic Validator...[/info]")
            is_valid = await self.validation_callback(agent_target, data)
            if not is_valid:
                console.print(
                    "[warning][!] SEMANTIC BREACH DETECTED -> Triggering Healing Protocol...[/warning]"
                )
                # Healing logic will be invoked here
            else:
                console.print(
                    "[success][+] PACKET VALID -> Allowing passthrough...[/success]"
                )

        return data


# Dummy test execution
async def run_dummy_traffic():
    console.print(
        Panel(
            "[bold bright_green]Initializing SentinelCell MAS Immune System...[/bold bright_green]",
            border_style="green",
        )
    )

    # Mock validator
    async def mock_validator(target: str, data: dict) -> bool:
        await asyncio.sleep(0.01)  # Simulate quick validation
        return "status" in data

    sniffer = TrafficSniffer(validation_callback=mock_validator)

    await asyncio.sleep(1)
    console.print("\n[dim cyan]Injecting valid traffic...[/dim cyan]")
    await sniffer.intercept(
        "Agent_Alpha", "Agent_Beta", '{"message": "Hello Beta", "status": "ok"}'
    )

    await asyncio.sleep(0.5)
    console.print(
        "\n[dim cyan]Injecting semantically invalid traffic (missing status)...[/dim cyan]"
    )
    await sniffer.intercept(
        "Agent_Gamma", "Agent_Delta", '{"message": "I am missing the status field"}'
    )

    await asyncio.sleep(0.5)
    console.print("\n[dim cyan]Injecting malformed JSON...[/dim cyan]")
    await sniffer.intercept(
        "Agent_Omega", "Agent_Zeta", '{"corrupted_data": "missing_keys",'
    )


if __name__ == "__main__":
    asyncio.run(run_dummy_traffic())
