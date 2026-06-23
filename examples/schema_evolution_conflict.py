import asyncio
import httpx
import os
from rich.console import Console

console = Console()


async def main():
    console.print("[bold cyan]Starting Schema Evolution Conflict Test...[/bold cyan]")
    api_key = os.getenv("API_KEY_SECRET", "")
    headers = {"Authorization": f"Bearer {api_key}"} if api_key else {}

    async with httpx.AsyncClient() as client:
        console.print(
            "[cyan]1. Sending payload assuming Schema v1 (First Name/Last Name)[/cyan]"
        )
        payload_v1 = '{"first_name": "John", "last_name": "Doe"}'
        res1 = await client.post(
            "http://localhost:8000/intercept?source=AgentA&target=UserDB",
            data=payload_v1,
            headers=headers,
        )
        console.print(f"Status: {res1.status_code}")

        console.print(
            "\n[cyan]2. Simulating Schema Upgrade to v2 (full_name required) via /schema/refresh[/cyan]"
        )
        await client.post("http://localhost:8000/schema/refresh", headers=headers)

        console.print(
            "\n[cyan]3. Sending an old in-flight v1 payload... Immune System should auto-migrate to v2![/cyan]"
        )
        res2 = await client.post(
            "http://localhost:8000/intercept?source=AgentA&target=UserDB",
            data=payload_v1,
            headers=headers,
        )
        console.print(f"Status: {res2.status_code}")
        if res2.status_code == 200:
            console.print(f"[bold green]Migrated Payload: {res2.text}[/bold green]")


if __name__ == "__main__":
    asyncio.run(main())
