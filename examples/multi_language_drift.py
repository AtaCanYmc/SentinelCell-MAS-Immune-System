import asyncio
import httpx
import os
from rich.console import Console

console = Console()


async def main():
    console.print(
        "[bold cyan]Starting Multi-Language Semantic Drift Test...[/bold cyan]"
    )
    api_key = os.getenv("API_KEY_SECRET", "")
    headers = {"Authorization": f"Bearer {api_key}"} if api_key else {}

    payload = '{"kullanici_adi": "admin_test", "sifre": "gizli123", "giris_sayisi": 5}'

    console.print(f"[cyan]Incoming Payload (Turkish): {payload}[/cyan]")
    console.print(
        "[cyan]Expected Schema Language: English (username, password, login_count)[/cyan]"
    )

    async with httpx.AsyncClient() as client:
        res = await client.post(
            "http://localhost:8000/intercept?source=AuthTR&target=AuthGlobal",
            data=payload,
            headers=headers,
        )
        console.print(f"Status: {res.status_code}")
        if res.status_code == 200:
            console.print(
                f"[bold green]Healed Payload (English): {res.text}[/bold green]"
            )
        else:
            console.print("[bold red]Translation / Healing Failed![/bold red]")


if __name__ == "__main__":
    asyncio.run(main())
