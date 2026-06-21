from src.core.logger import get_console

console = get_console()


class Sandbox:
    def execute(self, code: str):
        console.print("[hack][Sandbox][/hack] Executing isolated code...")
