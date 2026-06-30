import asyncio
import httpx
import uuid
import os
from rich.console import Console
from util import setup_mock_environment

setup_mock_environment()

console = Console()


async def main():
    from src.gateways.fastapi_gateway import app

    console.print(
        "[bold cyan]Starting Financial Transaction Idempotency Test...[/bold cyan]"
    )

    api_key = os.getenv("API_KEY_SECRET", "")

    idem_key = str(uuid.uuid4())
    headers = {"X-Idempotency-Key": idem_key}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    payload = '{"amount": "500.00", "currency": "USD"}'

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        console.print(
            f"[cyan]1. Sending Initial Transaction (Key: {idem_key})...[/cyan]"
        )
        res1 = await client.post(
            "/intercept?source=ATM&target=Ledger",
            data=payload,
            headers=headers,
        )
        console.print(f"Status: {res1.status_code}")

        console.print(
            "\n[cyan]2. Replaying SAME Transaction (Simulating Network Retry/Duplicate)...[/cyan]"
        )
        res2 = await client.post(
            "/intercept?source=ATM&target=Ledger",
            data=payload,
            headers=headers,
        )
        console.print(f"Status: {res2.status_code}")
        if res2.status_code == 208:
            console.print(
                "[bold green][+] SUCCESS: Idempotency Engine caught the duplicate and blocked processing![/bold green]"
            )
        else:
            console.print("[bold red][!] FAILED: Duplicate was processed![/bold red]")


if __name__ == "__main__":
    asyncio.run(main())
