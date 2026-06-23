import os
import sys
import subprocess
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.prompt import IntPrompt

# Terminal console styled for SentinelCell
console = Console()


def get_examples(examples_dir="examples"):
    """Lists executable Python files in the examples directory."""
    if not os.path.exists(examples_dir):
        return []

    # Filter out files like __init__.py
    files = [
        f
        for f in os.listdir(examples_dir)
        if f.endswith(".py") and not f.startswith("__")
    ]
    return sorted(files)


def main():
    examples_dir = "examples"
    examples = get_examples(examples_dir)

    if not examples:
        console.print(
            "[bold red][!] 'examples/' directory not found or empty.[/bold red]"
        )
        return

    # Create an elegant table in the terminal
    table = Table(
        title="🛡️ SentinelCell Simulation Command Center",
        show_header=True,
        header_style="bold cyan",
        border_style="cyan",
    )
    table.add_column("No", justify="center", style="dim", width=4)
    table.add_column("Simulation (Chaos/Drift/Injection)", style="bold green")

    for idx, file in enumerate(examples, start=1):
        table.add_row(str(idx), file.replace(".py", ""))

    console.clear()
    console.print(
        Panel(
            "[cyan]Select a simulation to test the immune system's responses.[/cyan]\n"
            "[dim]Press Ctrl+C to exit.[/dim]",
            border_style="cyan",
        )
    )
    console.print(table)

    try:
        # Get user input
        choices = [str(i) for i in range(1, len(examples) + 1)]
        choice = IntPrompt.ask(
            "\n[yellow][?] Simulation number to run[/yellow]",
            choices=choices,
        )

        selected_script = examples[choice - 1]
        script_path = os.path.join(examples_dir, selected_script)

        console.print(
            f"\n[bold magenta][*] Starting: {selected_script}...[/bold magenta]"
        )
        console.print("[dim]" + "─" * 60 + "[/dim]\n")

        # Set PYTHONPATH to the root directory (for proper module imports)
        env = os.environ.copy()
        env["PYTHONPATH"] = os.getcwd()

        # Run the script as a subprocess
        subprocess.run([sys.executable, script_path], env=env)

        console.print("\n[dim]" + "─" * 60 + "[/dim]")
        console.print("[bold green][+] Simulation completed.[/bold green]\n")

    except KeyboardInterrupt:
        console.print("\n[dim][*] Exiting...[/dim]\n")
    except Exception as e:
        console.print(f"\n[bold red][!] An unexpected error occurred: {e}[/bold red]\n")


if __name__ == "__main__":
    main()
