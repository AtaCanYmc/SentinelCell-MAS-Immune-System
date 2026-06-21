import asyncio
from src.core.logger import get_console

console = get_console()


class ConsumerAgent:
    def __init__(self, name: str):
        self.name = name

    async def receive(self, data: dict):
        console.print(f"[success][Consumer][/success] {self.name} received valid data.")
        await asyncio.sleep(0.1)
