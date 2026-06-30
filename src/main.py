import uvicorn
from rich.panel import Panel
from src.core.logger import get_console

console = get_console()


def main():
    console.print(
        Panel(
            "[bold bright_green]"
            "Initializing SentinelCell MAS Immune System (Production Mode)..."
            "[/bold bright_green]",
            border_style="green",
        )
    )
    # Start the FastAPI Guardian Gateway
    uvicorn.run(
        "src.gateways.fastapi_gateway:app",
        host="0.0.0.0",  # nosec B104
        port=8000,
        reload=False,
    )


if __name__ == "__main__":
    main()
