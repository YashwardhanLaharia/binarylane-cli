import os

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich import box

console = Console()


def clear_screen():
    os.system("cls" if os.name == "nt" else "clear")


def prompt_choice():
    return input("\nPress Enter to return to menu...")


def print_json(data: dict):
    console.print_json(data=data)


def make_info_table(items: list[tuple[str, str]]) -> Table:
    table = Table(show_header=False, box=box.SIMPLE, padding=(0, 2))
    table.add_column(style="yellow", width=20)
    table.add_column(style="white")
    for key, value in items:
        table.add_row(key, str(value))
    return table


def menu_panel(title: str, border_style: str = "blue") -> Panel:
    return Panel("", title=f"[bold yellow]{title}[/]", border_style=border_style, padding=(1, 2))


def format_kbps(kbps: float) -> str:
    if kbps >= 1000:
        return f"{kbps/1000:.2f} Mbps"
    return f"{kbps:.2f} Kbps"


def format_bytes_to_mb(bytes_val: float) -> str:
    return f"{bytes_val / (1024*1024):.2f} MB"


def format_bytes_to_gb(bytes_val: float) -> str:
    return f"{bytes_val / (1024*1024*1024):.2f} GB"