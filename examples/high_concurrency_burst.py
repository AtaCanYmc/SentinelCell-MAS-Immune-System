import asyncio
import httpx
import time
import os
from rich.console import Console

console = Console()


async def fetch(client, i, headers):
    try:
        await client.post(
            "http://localhost:8000/intercept?source=AgentB&target=InternalDB",
            data='{"foo": "bar"}',
            headers=headers,
        )
    except Exception:
        pass


async def main():
    console.print(
        "[bold cyan]Starting High Concurrency Burst (5000 requests)...[/bold cyan]"
    )
    api_key = os.getenv("API_KEY_SECRET", "")
    headers = {"Authorization": f"Bearer {api_key}"} if api_key else {}

    async with httpx.AsyncClient(limits=httpx.Limits(max_connections=1000)) as client:
        start = time.time()
        tasks = [fetch(client, i, headers) for i in range(5000)]
        await asyncio.gather(*tasks)
        total = time.time() - start
        console.print(
            f"[bold green]Completed 5000 requests in {total:.2f}s[/bold green]"
        )


if __name__ == "__main__":
    asyncio.run(main())
