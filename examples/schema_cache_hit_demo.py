import asyncio
import httpx
from src.gateways.fastapi_gateway import app
import time
import os
from rich.console import Console

console = Console()


async def main():
    console.print("[bold cyan]Starting Schema Cache Hit Demo...[/bold cyan]")
    api_key = os.getenv("API_KEY_SECRET", "")
    headers = {"Authorization": f"Bearer {api_key}"} if api_key else {}

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        # First request (should hit LLM)
        start = time.time()
        await client.post(
            "/intercept?source=AgentA&target=LedgerConsumer",
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
                "/intercept?source=AgentA&target=LedgerConsumer",
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
