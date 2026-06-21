import os
import time
from rich.panel import Panel
from src.skills.validation import SemanticValidator
from src.skills.repair import SelfHealingEngine
from src.core.logger import get_console
from src.mcp_integration.client import SchemaRegistryClient
from src.core.orchestrator import SentinelOrchestrator
from src.core.broadcaster import broadcaster

console = get_console()


class SentinelCell:
    def __init__(self):
        current_dir = os.path.dirname(os.path.abspath(__file__))
        registry_path = os.path.join(
            current_dir, "..", "mcp_integration", "registry.py"
        )
        self.mcp_client = SchemaRegistryClient(server_script_path=registry_path)

        self.validator = SemanticValidator(mcp_client=self.mcp_client)
        self.healer = SelfHealingEngine()

        # Instantiate the LangGraph Orchestrator
        self.orchestrator = SentinelOrchestrator(self.validator, self.healer)

        # Quarantine / Circuit Breaker State
        self.quarantine_mode = False
        self.quarantine_threshold = 5
        self.error_timestamps = []
        self.quarantine_cooldown_seconds = int(
            os.getenv("QUARANTINE_COOLDOWN_SECONDS", "30")
        )
        self.quarantine_timestamp = 0.0

    async def intercept(self, source: str, target: str, payload: str) -> dict | None:
        """
        Entry point for intercepting and routing traffic through the MAS Immune System.
        """
        now = time.time()

        if self.quarantine_mode:
            # Cool-down Check (Circuit Breaker Half-Open State)
            if now - self.quarantine_timestamp > self.quarantine_cooldown_seconds:
                console.print(
                    Panel.fit(
                        "[bold green]🔄 COOLDOWN COMPLETE 🔄[/bold green]\nInitiating Health Check... Allowing packet passthrough.",
                        border_style="green",
                    )
                )
                self.quarantine_mode = False
                self.error_timestamps.clear()
                await broadcaster.broadcast(
                    "SECURITY_ALERT", "QUARANTINE LIFTED - HEALTH CHECK INITIATED"
                )
            else:
                console.print(
                    Panel.fit(
                        "[bold red]⛔ SYSTEM IN QUARANTINE ⛔[/bold red]\nAll incoming traffic is being dropped automatically.",
                        border_style="red",
                    )
                )
                await broadcaster.broadcast(
                    "SECURITY_ALERT", "QUARANTINE BLOCKED TRAFFIC"
                )
                return None

        await broadcaster.broadcast(
            "INTERCEPT", f"Source: {source} -> Target: {target}"
        )

        result = await self.orchestrator.intercept(source, target, payload)

        if result is None:
            self.error_timestamps.append(time.time())
            # Sliding window of 60 seconds
            self.error_timestamps = [
                t for t in self.error_timestamps if time.time() - t < 60
            ]

            if len(self.error_timestamps) >= self.quarantine_threshold:
                if not self.quarantine_mode:
                    self.quarantine_mode = True
                    self.quarantine_timestamp = time.time()
                    console.print(
                        Panel.fit(
                            "[bold red]☢️ CRITICAL THREAT LEVEL ☢️[/bold red]\nToo many anomalies detected. Initiating Quarantine Lockdown!",
                            border_style="red",
                        )
                    )
                    await broadcaster.broadcast(
                        "SECURITY_ALERT", "SYSTEM LOCKDOWN: Quarantine Mode Engaged!"
                    )

        return result
