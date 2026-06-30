import orjson
import re
from src.core.logger import get_console

console = get_console()


class DeterministicHealer:
    """
    Attempts to repair JSON payloads using fast, rule-based heuristics
    before falling back to the more expensive LLM SelfHealingEngine.
    """

    async def repair_node(self, state: dict) -> dict:
        console.print("[dim cyan][*] Running Deterministic Healer...[/dim cyan]")

        payload = state.get("payload", {})
        schema = state.get("schema_dict", {})

        # Increment deterministic repair attempt counter
        deterministic_attempts = state.get("deterministic_repair_attempts", 0) + 1
        state["deterministic_repair_attempts"] = deterministic_attempts

        # 1. Handle Raw Unparsed Strings (e.g. single quotes instead of double quotes)
        if "_raw_unparsed_payload" in payload:
            raw_str = payload["_raw_unparsed_payload"]
            try:
                # Naive fix: replace single quotes with double quotes if not escaped
                fixed_str = re.sub(r"(?<!\\)'", '"', raw_str)
                repaired_payload = orjson.loads(fixed_str)
                console.print(
                    "[bold green][+] Deterministic Healer fixed raw JSON string![/bold green]"
                )
                state["payload"] = repaired_payload
                state["active_provider"] = "DETERMINISTIC_RULE_ENGINE"
                return state
            except Exception:
                pass
            return state  # Could not parse

        # 2. Schema-based Type Coercion
        if not schema or not isinstance(payload, dict):
            return state

        repaired_payload = dict(payload)
        made_changes = False

        properties = schema.get("properties", {})
        for key, expected_type_info in properties.items():
            if key in repaired_payload:
                val = repaired_payload[key]
                expected_type = expected_type_info.get("type")

                # Coerce String to Int/Float
                if expected_type == "integer" and isinstance(val, str):
                    try:
                        repaired_payload[key] = int(val)
                        made_changes = True
                    except ValueError:
                        pass
                elif expected_type == "number" and isinstance(val, str):
                    try:
                        repaired_payload[key] = float(val)
                        made_changes = True
                    except ValueError:
                        pass
                # Coerce Int/Float to String
                elif expected_type == "string" and isinstance(val, (int, float)):
                    repaired_payload[key] = str(val)
                    made_changes = True
                # Coerce to Boolean
                elif expected_type == "boolean" and isinstance(val, str):
                    lower_val = val.lower()
                    if lower_val in ["true", "1", "yes"]:
                        repaired_payload[key] = True
                        made_changes = True
                    elif lower_val in ["false", "0", "no"]:
                        repaired_payload[key] = False
                        made_changes = True

        if made_changes:
            console.print(
                "[bold green][+] Deterministic Healer coerced payload types based on schema![/bold green]"
            )
            state["payload"] = repaired_payload
            state["active_provider"] = "DETERMINISTIC_RULE_ENGINE"

        return state
