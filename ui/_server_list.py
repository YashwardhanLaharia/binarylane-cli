from rich.panel import Panel
from rich.table import Table
from rich import box

from client import BinaryLaneClient, BinaryLaneAPIError
from ui._components import clear_screen, console
from ui._server_details import show_server_details_menu


def show_servers_menu(client: BinaryLaneClient):
    clear_screen()

    try:
        servers = client.get_server_list()
    except BinaryLaneAPIError as e:
        console.print(f"[red]Error:[/] {e}")
        input("\nPress Enter to continue...")
        return

    if not servers:
        console.print("[yellow]No servers found.[/]")
        input("\nPress Enter to continue...")
        return

    table = Table(box=box.SIMPLE, padding=(0, 1))
    table.add_column("#", style="cyan", justify="right")
    table.add_column("Name", style="white", no_wrap=True)
    table.add_column("ID", style="dim", justify="right")
    table.add_column("Status")
    table.add_column("Region")
    table.add_column("OS")

    for i, server in enumerate(servers, 1):
        region = server.get("region", {})
        image = server.get("image", {})
        name = server.get("name", "Unknown")
        sid = server.get("id", "?")
        status = server.get("status", "unknown")
        status_style = {
            "active": "green",
            "off": "red",
            "new": "cyan",
        }.get(status, "white")
        region_name = region.get("slug", "?")
        os_name = image.get("distribution", "?")
        os_version = image.get("name", "")
        os_full = f"{os_name} {os_version}".strip()
        table.add_row(
            str(i),
            name,
            str(sid),
            f"[{status_style}]{status}[/]",
            region_name,
            os_full,
        )

    panel = Panel(
        table,
        title="[bold yellow]Your Servers[/]",
        border_style="blue",
        padding=(1, 2),
    )
    console.print(panel)
    console.print("[dim]0[/] Back to Main Menu")

    choice = input("Select a server by index: ").strip()

    if choice == "0":
        return

    try:
        idx = int(choice)
        if 1 <= idx <= len(servers):
            server_id = servers[idx - 1]["id"]
            show_server_details_menu(client, server_id)
        else:
            console.print("[red]Error:[/] Invalid index.")
            input("\nPress Enter to continue...")
    except ValueError:
        console.print("[red]Error:[/] Please enter a number.")
        input("\nPress Enter to continue...")