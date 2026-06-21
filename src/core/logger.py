from rich.console import Console
from rich.theme import Theme

# Hackerman theme for rich
custom_theme = Theme(
    {
        "info": "dim cyan",
        "warning": "magenta",
        "danger": "bold red",
        "success": "bold green",
        "hack": "bold bright_green",
    }
)
console = Console(theme=custom_theme)


def get_console():
    return console
