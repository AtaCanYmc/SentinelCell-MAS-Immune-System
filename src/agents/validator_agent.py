import os
import time
import redis.asyncio as redis
from rich.panel import Panel
from src.skills.validation import SemanticValidator
from src.skills.repair import SelfHealingEngine
from src.core.logger import get_console
from src.mcp_integration.client import SchemaRegistryClient
from src.core.orchestrator import SentinelOrchestrator
from src.core.broadcaster import broadcaster
from src.core.tracer import get_tracer

console = get_console()
tracer = get_tracer()


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

        # Distributed State config
        self.redis_client = None
        redis_url = os.getenv("REDIS_URL")
        if redis_url:
            self.redis_client = redis.from_url(redis_url)

        self.quarantine_threshold = int(os.getenv("QUARANTINE_ERROR_THRESHOLD", "5"))
        self.quarantine_cooldown_seconds = int(
            os.getenv("QUARANTINE_COOLDOWN_SECONDS", "30")
        )
        self.quarantine_window = int(os.getenv("QUARANTINE_WINDOW_SECONDS", "60"))

        # Fallback local state if Redis not available
        self._local_quarantine_mode = False
        self._local_error_timestamps = []
        self._local_quarantine_timestamp = 0.0

    async def _get_quarantine_state(self):
        if self.redis_client:
            try:
                q_mode = await self.redis_client.get("sentinel:quarantine:mode")
                q_ts = await self.redis_client.get("sentinel:quarantine:timestamp")
                return (q_mode == b"1", float(q_ts) if q_ts else 0.0)
            except Exception:
                pass
        return (self._local_quarantine_mode, self._local_quarantine_timestamp)

    async def _set_quarantine_state(self, mode: bool):
        from src.core.telemetry import metrics

        metrics.quarantine_status.set(1.0 if mode else 0.0)
        now = time.time()
        if self.redis_client:
            try:
                await self.redis_client.set(
                    "sentinel:quarantine:mode", "1" if mode else "0"
                )
                if mode:
                    await self.redis_client.set(
                        "sentinel:quarantine:timestamp", str(now)
                    )
                else:
                    await self.redis_client.delete("sentinel:quarantine:errors")
                return
            except Exception:
                pass

        self._local_quarantine_mode = mode
        if mode:
            self._local_quarantine_timestamp = now
        else:
            self._local_error_timestamps.clear()

    async def _record_error_and_check(self) -> bool:
        """Returns True if threshold exceeded (should quarantine)."""
        now = time.time()
        if self.redis_client:
            try:
                key = "sentinel:quarantine:errors"
                await self.redis_client.zadd(key, {str(now): now})
                await self.redis_client.zremrangebyscore(
                    key, 0, now - self.quarantine_window
                )
                count = await self.redis_client.zcard(key)
                return count >= self.quarantine_threshold
            except Exception:
                pass

        self._local_error_timestamps.append(now)
        self._local_error_timestamps = [
            t for t in self._local_error_timestamps if now - t < self.quarantine_window
        ]
        return len(self._local_error_timestamps) >= self.quarantine_threshold

    async def intercept(
        self, source: str, target: str, payload: str, context: dict | None = None
    ) -> dict | None:
        """
        Entry point for intercepting and routing traffic through the MAS Immune System.
        """
        with tracer.start_as_current_span("SentinelCell.Intercept") as span:
            span.set_attribute("sentinel.source", source)
            span.set_attribute("sentinel.target", target)
            return await self._intercept_internal(source, target, payload, context)

    async def _intercept_internal(
        self, source: str, target: str, payload: str, context: dict | None = None
    ) -> dict | None:
        now = time.time()
        q_mode, q_ts = await self._get_quarantine_state()

        if q_mode:
            # Cool-down Check (Circuit Breaker Half-Open State)
            if now - q_ts > self.quarantine_cooldown_seconds:
                console.print(
                    Panel.fit(
                        "[bold green]🔄 COOLDOWN COMPLETE 🔄[/bold green]\nInitiating Health Check... Allowing packet passthrough.",
                        border_style="green",
                    )
                )
                await self._set_quarantine_state(False)
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

        result = await self.orchestrator.intercept(
            source, target, payload, context=context
        )

        if result is None:
            should_quarantine = await self._record_error_and_check()
            if should_quarantine:
                current_q_mode, _ = await self._get_quarantine_state()
                if not current_q_mode:
                    await self._set_quarantine_state(True)
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
