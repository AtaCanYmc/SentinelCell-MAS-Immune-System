import asyncio
import httpx
import time
import os
from rich.console import Console

console = Console()


async def main():
    console.print("[bold cyan]Starting Schema Cache Hit Demo...[/bold cyan]")
    api_key = os.getenv("API_KEY_SECRET", "")
    headers = {"Authorization": f"Bearer {api_key}"} if api_key else {}

    async with httpx.AsyncClient() as client:
        # First request (should hit LLM)
        start = time.time()
        await client.post(
            "http://localhost:8000/intercept?source=AgentA&target=LedgerConsumer",
            data='{"amount": "100"}',
            headers=headers,
        )
        first_lat = time.time() - start
        console.print(
            f"[bold yellow]First Request Latency (LLM): {first_lat*1000:.2f} ms[/bold yellow]"
        )

        # 100 fast requests
        console.print("[cyan]Sending 100 identical malformed payloads...[/cyan]")
        start = time.time()
        for i in range(100):
            await client.post(
                "http://localhost:8000/intercept?source=AgentA&target=LedgerConsumer",
                data='{"amount": "100"}',
                headers=headers,
            )
        total_lat = time.time() - start
        console.print(
            f"[bold green]100 Cached Requests Total Latency: {total_lat*1000:.2f} ms[/bold green]"
        )
        console.print(
            f"[bold green]Average Cached Latency: {(total_lat/100)*1000:.2f} ms[/bold green]"
        )


if __name__ == "__main__":
    asyncio.run(main())
