import os
import json
import asyncio
import redis.asyncio as redis
from src.agents.validator_agent import SentinelCell
from rich.console import Console

console = Console()


async def mq_worker():
    redis_url = os.getenv("REDIS_URL", "redis://redis:6379")
    client = redis.from_url(redis_url)
    sentinel = SentinelCell()

    console.print(
        f"[bold cyan]SentinelCell Redis MQ Worker started on {redis_url}[/bold cyan]"
    )

    while True:
        try:
            # blpop blocks until a message is available in 'sentinel.in'
            message = await client.blpop("sentinel.in", timeout=0)
            if message:
                queue_name, raw_data = message
                data_str = raw_data.decode("utf-8")

                # We expect the payload to be wrapped with source and target info for routing
                # Example: {"source": "AgentA", "target": "AgentB", "payload": "{\"status\":\"ok\"}"}
                try:
                    envelope = json.loads(data_str)
                    source = envelope.get("source", "Unknown")
                    target = envelope.get("target", "Unknown")
                    payload = envelope.get("payload", data_str)

                    if isinstance(payload, dict):
                        payload = json.dumps(payload)

                    result = await sentinel.intercept(
                        source=source, target=target, payload=payload
                    )

                    if result:
                        # Push the valid/healed message to 'sentinel.out'
                        await client.rpush("sentinel.out", json.dumps(result))
                        console.print(
                            "[green]Message processed and forwarded to sentinel.out[/green]"
                        )
                    else:
                        console.print("[red]Message rejected and dropped.[/red]")

                except json.JSONDecodeError:
                    console.print(
                        "[red]Invalid envelope format. Dropping message.[/red]"
                    )

        except Exception as e:
            console.print(f"[bold red]Worker Error: {e}[/bold red]")
            await asyncio.sleep(5)


if __name__ == "__main__":
    asyncio.run(mq_worker())
