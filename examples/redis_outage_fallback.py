import asyncio
import os
from src.skills.repair import SelfHealingEngine
from rich.console import Console
from util import setup_mock_environment

setup_mock_environment()

console = Console()


async def main():
    console.print(
        "[bold red][!] SIMULATING REDIS OUTAGE: Removing REDIS_URL from env[/bold red]"
    )
    if "REDIS_URL" in os.environ:
        del os.environ["REDIS_URL"]

    healer = SelfHealingEngine()

    state = {
        "schema_dict": {"title": "TestSchema"},
        "payload": {"malformed": "data"},
        "repair_attempts": 0,
        "error_context": "Test Error",
    }

    console.print("[bold cyan][*] Injecting to In-Memory Cache...[/bold cyan]")
    if not hasattr(healer, "_semantic_cache"):
        healer._semantic_cache = {}

    import hashlib
    import orjson

    payload_hash = hashlib.sha256(
        orjson.dumps(state["payload"], option=orjson.OPT_SORT_KEYS)
    ).hexdigest()
    cache_key = f"sentinel:semantic_cache:TestSchema:{payload_hash}"
    healer._semantic_cache[cache_key] = {"malformed": "fixed"}

    console.print(
        "[bold cyan][*] Running repair (Should hit In-Memory Cache despite Redis outage)...[/bold cyan]"
    )
    result = await healer.repair_node(state)

    if result.get("active_provider") == "CACHE":
        console.print(
            "[bold green][+] SUCCESS: In-Memory Semantic Cache fallback worked![/bold green]"
        )
        console.print(result["payload"])
    else:
        console.print(
            "[bold red][!] FAILURE: Cache fallback did not trigger.[/bold red]"
        )


if __name__ == "__main__":
    asyncio.run(main())
