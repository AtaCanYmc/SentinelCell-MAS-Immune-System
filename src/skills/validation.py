import asyncio
import os
import jsonschema
from rich.console import Console
from rich.panel import Panel
from src.mcp_integration.client import SchemaRegistryClient
from src.core.tracer import get_tracer

console = Console()
tracer = get_tracer()


class SecuritySanitizer:
    MALICIOUS_PATTERNS = [
        "ignore previous",
        "system prompt",
        "external_ip",
        "eval(",
        "exec(",
    ]

    @classmethod
    def check_payload(cls, data: dict) -> str | None:
        import base64

        def _check_string(val: str) -> str | None:
            val_lower = val.lower()
            for pattern in cls.MALICIOUS_PATTERNS:
                if pattern in val_lower:
                    return f"SECURITY_BREACH: Adversarial Prompt Injection Detected (Pattern: '{pattern}')"

            try:
                padded = val + "=" * (-len(val) % 4)
                decoded = (
                    base64.b64decode(padded, validate=True).decode("utf-8").lower()
                )
                for pattern in cls.MALICIOUS_PATTERNS:
                    if pattern in decoded:
                        return f"SECURITY_BREACH: Obfuscated (Base64) Prompt Injection Detected (Pattern: '{pattern}')"
            except Exception:
                pass

            try:
                decoded = bytes.fromhex(val).decode("utf-8").lower()
                for pattern in cls.MALICIOUS_PATTERNS:
                    if pattern in decoded:
                        return f"SECURITY_BREACH: Obfuscated (Hex) Prompt Injection Detected (Pattern: '{pattern}')"
            except Exception:
                pass
            return None

        import os

        max_depth = int(os.getenv("MAX_PAYLOAD_DEPTH", "20"))
        max_keys = int(os.getenv("MAX_PAYLOAD_KEYS", "1000"))
        key_count = [0]

        def _traverse(obj, current_depth=1) -> str | None:
            if current_depth > max_depth:
                return f"SECURITY_BREACH: JSON Depth Exceeded ({current_depth} > {max_depth})"

            if isinstance(obj, dict):
                key_count[0] += len(obj.keys())
                if key_count[0] > max_keys:
                    return f"SECURITY_BREACH: JSON Key Count Exceeded ({key_count[0]} > {max_keys})"
                for v in obj.values():
                    res = _traverse(v, current_depth + 1)
                    if res:
                        return res
            elif isinstance(obj, list):
                for v in obj:
                    res = _traverse(v, current_depth + 1)
                    if res:
                        return res
            elif isinstance(obj, str):
                return _check_string(obj)
            return None

        # Fallback check on full string representation
        data_str = str(data).lower()
        for pattern in cls.MALICIOUS_PATTERNS:
            if pattern in data_str:
                return f"SECURITY_BREACH: Adversarial Prompt Injection Detected (Pattern: '{pattern}')"

        return _traverse(data)


class FinancialDriftGuard:
    _history = {}
    WINDOW_SIZE = 10
    SIGMA_MULTIPLIER = 3.0
    FINANCIAL_KEYS = {"amount", "price", "balance", "total", "value"}

    @classmethod
    def check_anomaly(cls, target: str, payload: dict) -> str | None:
        import math

        target_history = cls._history.setdefault(target, {})

        def _check_dict(d: dict):
            for key, value in d.items():
                if isinstance(value, dict):
                    res = _check_dict(value)
                    if res:
                        return res
                elif isinstance(value, list):
                    for item in value:
                        if isinstance(item, dict):
                            res = _check_dict(item)
                            if res:
                                return res
                elif (
                    isinstance(value, (int, float))
                    and key.lower() in cls.FINANCIAL_KEYS
                ):
                    history = target_history.setdefault(key, [])
                    if len(history) >= 3:
                        mean = sum(history) / len(history)
                        variance = sum((x - mean) ** 2 for x in history) / len(history)
                        std_dev = math.sqrt(variance)

                        # Minimum std dev to prevent infinite anomaly if past values are identical
                        std_dev = max(std_dev, abs(mean * 0.05))

                        if std_dev > 0:
                            drift = abs(value - mean)
                            if drift > cls.SIGMA_MULTIPLIER * std_dev:
                                return f"FINANCIAL_ANOMALY: {key} value {value} deviates from mean {mean:.2f} by >{cls.SIGMA_MULTIPLIER} sigma"

                    history.append(value)
                    if len(history) > cls.WINDOW_SIZE:
                        history.pop(0)
            return None

        return _check_dict(payload)


class SemanticValidator:
    """
    Semantic Integrity Engine based on JSON Schema (via MCP).
    """

    def __init__(self, mcp_client: SchemaRegistryClient):
        import os

        self.mcp_client = mcp_client
        self._cache = {}  # In-memory cache: {agent_target: {"schema": dict, "expires_at": float}}
        self.cache_ttl = int(os.getenv("SCHEMA_CACHE_TTL_SECONDS", "300"))
        self.dynamic_skills = self._load_dynamic_skills()

        from src.skills.schema_inference import AutoSchemaInferencer

        self.schema_inferencer = AutoSchemaInferencer(
            mcp_client=self.mcp_client, on_schema_registered_cb=self.clear_cache
        )

    def _load_dynamic_skills(self):
        import yaml
        import os

        skills_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "skills.yaml"
        )
        if os.path.exists(skills_path):
            try:
                with open(skills_path, "r") as f:
                    data = yaml.safe_load(f)
                    return data.get("skills", [])
            except Exception as e:
                console.print(
                    f"[bold red]Failed to load dynamic skills: {e}[/bold red]"
                )
        return []

    async def _get_schema(self, agent_target: str) -> dict | None:
        import time

        now = time.time()

        if agent_target in self._cache:
            cache_entry = self._cache[agent_target]
            if now < cache_entry["expires_at"]:
                return cache_entry["schema"]

        # Fetch from MCP server
        console.print(
            f"[dim]Fetching schema from MCP Registry for {agent_target}...[/dim]"
        )
        try:
            with tracer.start_as_current_span("MCP.FetchSchema") as span:
                span.set_attribute("mcp.agent_target", agent_target)
                schema = await self.mcp_client.fetch_schema(agent_target)
        except Exception as e:
            import os

            # Circuit Breaker: Try Stale Cache first
            if agent_target in self._cache:
                console.print(
                    f"[bold yellow][!] MCP Registry Error: {e}. CIRCUIT BREAKER engaged. Using STALE cache for {agent_target}.[/bold yellow]"
                )
                return self._cache[agent_target]["schema"]

            policy = os.getenv("MCP_FAILURE_POLICY", "FAIL_OPEN").upper()
            if policy == "FAIL_CLOSED":
                console.print(
                    f"[bold red][!] MCP Registry Error: {e}. FAIL_CLOSED engaged. Blocking traffic.[/bold red]"
                )
                raise RuntimeError("MCP_FAILURE")
            else:
                console.print(
                    f"[bold red][!] MCP Registry Error: {e}. Fail-Open engaged, passing traffic.[/bold red]"
                )
                return None

        # Update cache
        self._cache[agent_target] = {
            "schema": schema,
            "expires_at": now + self.cache_ttl,
        }
        return schema

    def clear_cache(self, agent_target: str = None):
        """
        Clears the schema cache. If agent_target is provided, clears only that target.
        """
        self.dynamic_skills = self._load_dynamic_skills()
        if agent_target:
            self._cache.pop(agent_target, None)
            console.print(
                f"[dim cyan][*] Cache cleared for agent: {agent_target}[/dim cyan]"
            )
        else:
            self._cache.clear()
            console.print("[dim cyan][*] Schema cache completely purged[/dim cyan]")

    async def validate_packet(self, agent_target: str, data: dict) -> bool:
        """
        Validates the incoming data against the target agent's schema.
        Returns True if valid, False if invalid.
        Raises ValueError if no schema is found but we expect one, though for now we pass through.
        """
        try:
            schema = await self._get_schema(agent_target)
        except RuntimeError:
            return False

        if not schema:
            # Check Observation Mode
            if os.getenv("OBSERVATION_MODE", "false").lower() == "true":
                console.print(
                    f"[dim yellow][?] No contract found for {agent_target}. Observation Mode Active -> Bypassing.[/dim yellow]"
                )
                return True

            console.print(
                f"[bold red][!] ZERO-TRUST: No contract found for target: {agent_target}. Traffic rejected![/bold red]"
            )
            return False

        try:
            # Simulate non-intrusive fast processing
            await asyncio.sleep(0.005)
            jsonschema.validate(instance=data, schema=schema)
            return True
        except jsonschema.ValidationError as e:
            console.print(
                Panel(
                    f"[bold red]Validation Error:[/bold red]\n{e.message}",
                    title="[!] Schema Mismatch",
                    border_style="red",
                )
            )
            return False

    async def validate_and_get_schema(
        self, agent_target: str, data: dict
    ) -> tuple[bool, dict | None, str | None]:
        """
        Helper for healer: Returns (is_valid, schema_dict, error_context)
        """
        # 1. Get Schema
        try:
            schema = await self._get_schema(agent_target)
        except RuntimeError:
            return False, None, "MCP Registry Unavailable"

        if not schema:
            # Check Observation Mode
            if os.getenv("OBSERVATION_MODE", "false").lower() == "true":
                self.schema_inferencer.observe(agent_target, data)
                return True, None, None

            console.print(
                f"[bold red][!] ZERO-TRUST: No contract found for target: {agent_target}. Traffic rejected![/bold red]"
            )
            return False, None, "Zero-Trust: Missing Schema"

        # 2. Active Security Shield (Sanitizer)
        from src.core.broadcaster import broadcaster

        security_error = SecuritySanitizer.check_payload(data)
        if security_error:
            await broadcaster.broadcast("SECURITY_ALERT", security_error)
            return False, schema, security_error

        # 2.5 Financial Drift Guard
        financial_anomaly = FinancialDriftGuard.check_anomaly(agent_target, data)
        if financial_anomaly:
            await broadcaster.broadcast("FINANCIAL_ALERT", financial_anomaly)
            return False, schema, financial_anomaly

        # 3. Schema Validation
        try:
            jsonschema.validate(instance=data, schema=schema)

            # 4. Dynamic Skills Evaluation
            for skill in self.dynamic_skills:
                if skill.get("target") == agent_target or skill.get("target") == "*":
                    condition = skill.get("condition", "")
                    try:
                        import json

                        if not eval(condition, {"payload": data, "json": json}):
                            return (
                                False,
                                schema,
                                f"Dynamic Skill '{skill['name']}' Failed: {skill['error_message']}",
                            )
                    except Exception as e:
                        console.print(
                            f"[dim yellow]Dynamic skill eval error ({skill['name']}): {e}[/dim yellow]"
                        )

            return True, schema, None
        except jsonschema.ValidationError as e:
            return False, schema, e.message

    async def validate_node(self, state: dict) -> dict:
        """
        LangGraph node execution for validation.
        """
        target = state.get("agent_target", "")
        data = state.get("payload", {})
        console.print(f"[info][SentinelCell][/info] Validating data for {target}...")
        is_valid, schema, error_context = await self.validate_and_get_schema(
            target, data
        )
        if not is_valid:
            console.print(
                Panel(
                    f"[bold red]Validation Error:[/bold red]\n{error_context}",
                    title="[!] Schema Mismatch",
                    border_style="red",
                )
            )
        return {
            "is_valid": is_valid,
            "schema_dict": schema,
            "error_context": error_context,
        }
