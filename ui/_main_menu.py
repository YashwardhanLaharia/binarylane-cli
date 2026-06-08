import sys

from rich.panel import Panel
from rich.table import Table
from rich import box

from client import BinaryLaneClient, BinaryLaneAPIError, BinaryLaneValidationError
from ui._components import clear_screen, console, make_info_table, prompt_choice
from ui._server_list import show_servers_menu
from ui._speedtest import run_speedtest


def show_main_menu():
    clear_screen()
    table = Table(show_header=False, box=box.SIMPLE, padding=(0, 2))
    table.add_column(style="cyan", justify="right", width=2)
    table.add_column("")
    table.add_row("1.", "Account Info")
    table.add_row("2.", "Servers")
    table.add_row("3.", "List Recent Actions")
    table.add_row("4.", "Perform Server Action")
    table.add_row("5.", "Speedtest (Local to VPS)")
    table.add_row("Q.", "Quit")
    panel = Panel(
        table,
        title="[bold yellow]BinaryLane API CLI[/]",
        border_style="blue",
        padding=(1, 2),
    )
    console.print(panel)


def run_main_choice(client: BinaryLaneClient, choice: str):
    if choice == "1":
        clear_screen()
        try:
            data = client.get_account()
            account = data.get("account", data)
            items = [
                ("Name:", account.get("name", "")),
                ("Email:", account.get("email", "")),
                ("UUID:", account.get("uuid", "")),
                ("Status:", account.get("status", "")),
                ("Email Verified:", str(account.get("email_verified", ""))),
                ("Created At:", account.get("created_at", "")),
            ]
            t = make_info_table(items)
            console.print(Panel(t, title="[bold]Account Info[/]", border_style="blue", padding=(1, 2)))
        except BinaryLaneAPIError as e:
            console.print(f"[red]Error:[/] {e}")
        prompt_choice()

    elif choice == "2":
        show_servers_menu(client)

    elif choice == "3":
        clear_screen()
        try:
            data = client.list_actions()
            actions = data.get("actions", [])
            if not actions:
                console.print("[yellow]No recent actions found.[/]")
            else:
                table = Table(box=box.SIMPLE, padding=(0, 1))
                table.add_column("ID", style="cyan", justify="right")
                table.add_column("Type", style="white")
                table.add_column("Status")
                table.add_column("Region")
                table.add_column("Started")
                table.add_column("Completed")
                for action in actions:
                    sid = action.get("id", "")
                    atype = action.get("type", "")
                    status = action.get("status", "")
                    region = action.get("region_slug", "")
                    started = action.get("started_at", "")
                    completed = action.get("completed_at", "") or "[dim]pending[/]"
                    status_style = {
                        "completed": "green",
                        "in-progress": "cyan",
                        "errored": "red",
                        "new": "dim",
                    }.get(status, "white")
                    table.add_row(
                        str(sid),
                        atype,
                        f"[{status_style}]{status}[/]",
                        region,
                        str(started)[:19],
                        str(completed)[:19],
                    )
                console.print(Panel(table, title="[bold]Recent Actions[/]", border_style="blue", padding=(1, 2)))
        except BinaryLaneAPIError as e:
            console.print(f"[red]Error:[/] {e}")
        prompt_choice()

    elif choice == "4":
        clear_screen()

        try:
            servers = client.get_server_list()
        except BinaryLaneAPIError as e:
            console.print(f"[red]Error:[/] {e}")
            prompt_choice()
            return

        if not servers:
            console.print("[yellow]No servers found.[/]")
            prompt_choice()
            return

        table = Table(box=box.SIMPLE, padding=(0, 1))
        table.add_column("#", style="cyan", justify="right")
        table.add_column("Name")
        table.add_column("ID", justify="right")
        for i, server in enumerate(servers, 1):
            table.add_row(str(i), server["name"], str(server["id"]))
        console.print(Panel(table, title="[bold]Select Server[/]", border_style="blue", padding=(1, 2)))
        console.print("[dim]0[/] Cancel")

        s_choice = input("Select a server by index: ").strip()
        if s_choice == "0":
            return

        try:
            idx = int(s_choice)
            if not (1 <= idx <= len(servers)):
                console.print("[red]Error:[/] Invalid index.")
                prompt_choice()
                return
            server_id = servers[idx - 1]["id"]
        except ValueError:
            console.print("[red]Error:[/] Please enter a number.")
            prompt_choice()
            return

        clear_screen()
        action_type = input("Enter action type (e.g., reboot, power_on, power_off): ").strip()
        if not action_type:
            console.print("[red]Error:[/] Action type required.")
            prompt_choice()
            return
        try:
            result = client.perform_server_action(server_id, action_type)
            action = result.get("action", result)
            items = [
                ("Action ID:", str(action.get("id", ""))),
                ("Type:", action.get("type", "")),
                ("Status:", action.get("status", "")),
                ("Started:", str(action.get("started_at", ""))),
                ("Completed:", str(action.get("completed_at", ""))),
                ("Region:", action.get("region_slug", "")),
            ]
            t = make_info_table(items)
            console.print(Panel(t, title="[bold]Action Result[/]", border_style="green", padding=(1, 2)))
        except BinaryLaneValidationError as e:
            console.print(f"[red]Validation error:[/] {e}")
            if e.response_data:
                console.print(e.response_data)
        except BinaryLaneAPIError as e:
            console.print(f"[red]Error:[/] {e}")
        prompt_choice()

    elif choice == "5":
        run_speedtest(client)

    elif choice.lower() == "q":
        clear_screen()
        console.print("[bold green]Goodbye![/]")
        sys.exit(0)

    else:
        clear_screen()
        console.print("[red]Invalid option. Press Enter to continue...[/]")
        input()