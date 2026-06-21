import asyncio
from src.core.logger import get_console

console = get_console()


class ProducerAgent:
    def __init__(self, name: str):
        self.name = name

    async def emit(self, data: str):
        console.print(f"[info][Producer][/info] {self.name} emitting data...")
        await asyncio.sleep(0.1)
        return data
