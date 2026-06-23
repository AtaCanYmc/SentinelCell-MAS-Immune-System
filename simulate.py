import os
import sys
import subprocess
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.prompt import IntPrompt

# SentinelCell temasına uygun terminal konsolu
console = Console()


def get_examples(examples_dir="examples"):
    """Examples klasöründeki çalıştırılabilir Python dosyalarını listeler."""
    if not os.path.exists(examples_dir):
        return []

    # __init__.py gibi dosyaları filtrele
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
            "[bold red][!] 'examples/' klasörü bulunamadı veya içi boş.[/bold red]"
        )
        return

    # Terminalde şık bir tablo oluştur
    table = Table(
        title="🛡️ SentinelCell Simülasyon Komuta Merkezi",
        show_header=True,
        header_style="bold cyan",
        border_style="cyan",
    )
    table.add_column("No", justify="center", style="dim", width=4)
    table.add_column("Simülasyon (Chaos/Drift/Injection)", style="bold green")

    for idx, file in enumerate(examples, start=1):
        table.add_row(str(idx), file.replace(".py", ""))

    console.clear()
    console.print(
        Panel(
            "[cyan]Sistemin bağışıklık tepkilerini test etmek için bir simülasyon seçin.[/cyan]\n"
            "[dim]Çıkmak için Ctrl+C'ye basabilirsiniz.[/dim]",
            border_style="cyan",
        )
    )
    console.print(table)

    try:
        # Kullanıcıdan giriş al
        choices = [str(i) for i in range(1, len(examples) + 1)]
        choice = IntPrompt.ask(
            "\n[yellow][?] Çalıştırmak istediğiniz simülasyon numarası[/yellow]",
            choices=choices,
        )

        selected_script = examples[choice - 1]
        script_path = os.path.join(examples_dir, selected_script)

        console.print(
            f"\n[bold magenta][*] Başlatılıyor: {selected_script}...[/bold magenta]"
        )
        console.print("[dim]" + "─" * 60 + "[/dim]\n")

        # PYTHONPATH'i ana dizine ayarla (modüllerin düzgün içe aktarılması için)
        env = os.environ.copy()
        env["PYTHONPATH"] = os.getcwd()

        # Scripti alt süreç (subprocess) olarak çalıştır
        subprocess.run([sys.executable, script_path], env=env)

        console.print("\n[dim]" + "─" * 60 + "[/dim]")
        console.print("[bold green][+] Simülasyon tamamlandı.[/bold green]\n")

    except KeyboardInterrupt:
        console.print("\n[dim][*] Çıkış yapılıyor...[/dim]\n")
    except Exception as e:
        console.print(f"\n[bold red][!] Beklenmeyen bir hata oluştu: {e}[/bold red]\n")


if __name__ == "__main__":
    main()
