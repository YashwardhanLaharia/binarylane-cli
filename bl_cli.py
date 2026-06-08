import os
import sys
import json

import requests
from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, BarColumn, TextColumn
from rich import box

console = Console()

# --- Custom Exceptions ---


class BinaryLaneAPIError(Exception):
    """Base exception for BinaryLane API errors."""

    def __init__(self, message, status_code=None, response_data=None):
        super().__init__(message)
        self.status_code = status_code
        self.response_data = response_data


class BinaryLaneAuthError(BinaryLaneAPIError):
    """Raised on 401 Unauthorized."""

    pass


class BinaryLaneNotFound(BinaryLaneAPIError):
    """Raised on 404 Not Found."""

    pass


class BinaryLaneValidationError(BinaryLaneAPIError):
    """Raised on 400 Bad Request or validation errors."""

    pass


# --- Client ---


class BinaryLaneClient:
    def __init__(self, api_token: str, base_url: str = "https://api.binarylane.com.au"):
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()
        self.session.headers.update(
            {
                "Authorization": f"Bearer {api_token}",
                "Content-Type": "application/json",
            }
        )

    def _request(self, method: str, path: str, **kwargs) -> dict:
        if not path.startswith("/"):
            path = "/" + path
        url = f"{self.base_url}{path}"

        response = self.session.request(method, url, **kwargs)

        if response.status_code == 401:
            raise BinaryLaneAuthError(
                "Authentication failed. Check your API token.",
                status_code=401,
                response_data=response.text,
            )
        elif response.status_code == 404:
            raise BinaryLaneNotFound(
                f"Resource not found: {path}",
                status_code=404,
                response_data=response.text,
            )
        elif response.status_code == 400:
            raise BinaryLaneValidationError(
                "Validation error. Check your request.",
                status_code=400,
                response_data=response.text,
            )

        response.raise_for_status()

        if response.status_code == 204:
            return {}
        return response.json()

    # Account
    def get_account(self) -> dict:
        return self._request("GET", "/v2/account")

    # Servers
    def list_servers(self, page: int = 1, per_page: int = 20) -> dict:
        params = {"page": page, "per_page": per_page}
        return self._request("GET", "/v2/servers", params=params)

    def get_server(self, server_id: int) -> dict:
        return self._request("GET", f"/v2/servers/{server_id}")

    # Actions
    def list_actions(self, page: int = 1, per_page: int = 20) -> dict:
        params = {"page": page, "per_page": per_page}
        return self._request("GET", "/v2/actions", params=params)

    def perform_server_action(self, server_id: int, action_type: str, **kwargs) -> dict:
        payload = {"type": action_type, **kwargs}
        return self._request("POST", f"/v2/servers/{server_id}/actions", json=payload)

    # Helpers
    def get_server_list(self) -> list:
        """Convenience: returns just the list of server dicts."""
        data = self.list_servers()
        return data.get("servers", [])

    # Data Usage
    def get_data_usage(self, server_id: int) -> dict:
        return self._request("GET", f"/v2/data_usages/{server_id}/current")

    # Performance / Sample Sets
    def get_latest_sample_set(
        self, server_id: int, data_interval: str = "five-minute"
    ) -> dict:
        params = {"data_interval": data_interval}
        return self._request("GET", f"/v2/samplesets/{server_id}/latest", params=params)


# --- UI Helpers ---


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


# --- Menus ---


def show_main_menu():
    clear_screen()
    console = Console()
    table = Table(show_header=False, box=box.SIMPLE, padding=(0, 2))
    table.add_column(style="cyan", justify="right", width=2)
    table.add_column("")
    table.add_row("1.", "Account Info")
    table.add_row("2.", "Servers")
    table.add_row("3.", "List Recent Actions")
    table.add_row("4.", "Perform Server Action")
    table.add_row("Q.", "Quit")
    panel = Panel(
        table,
        title="[bold yellow]BinaryLane API CLI[/]",
        border_style="blue",
        padding=(1, 2),
    )
    console.print(panel)


def show_servers_menu(client: BinaryLaneClient):
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
            prompt_choice()
    except ValueError:
        console.print("[red]Error:[/] Please enter a number.")
        prompt_choice()


def show_server_details_menu(client: BinaryLaneClient, server_id: int):
    try:
        data = client.get_server(server_id)
    except BinaryLaneAPIError as e:
        console.print(f"[red]Error fetching server details:[/] {e}")
        prompt_choice()
        return

    server = data.get("server", {})
    if not server:
        console.print("[red]No server data returned.[/]")
        prompt_choice()
        return

    while True:
        clear_screen()
        server_name = server.get("name", "Unknown")
        table = Table(show_header=False, box=box.SIMPLE, padding=(0, 2))
        table.add_column(style="cyan", justify="right", width=2)
        table.add_column("")
        table.add_row("1.", "Basic Info")
        table.add_row("2.", "Specifications")
        table.add_row("3.", "Networking")
        table.add_row("4.", "Region & Operating System")
        table.add_row("5.", "Backups & Maintenance")
        table.add_row("6.", "Full JSON")
        table.add_row("7.", "Performance & Usage")
        table.add_row("8.", "Back to Main Menu")
        panel = Panel(
            table,
            title=f"[bold yellow]Server: {server_name}[/]",
            border_style="blue",
            padding=(1, 2),
        )
        console.print(panel)

        choice = input("Select an option: ").strip()

        if choice == "1":
            clear_screen()
            t = make_info_table([
                ("ID:", str(server.get("id", ""))),
                ("Hostname:", server.get("name", "")),
                ("Status:", server.get("status", "")),
                ("Created At:", server.get("created_at", "")),
                ("Permalink:", server.get("permalink", "")),
                ("Password Change Supported:", str(server.get("password_change_supported", ""))),
            ])
            console.print(Panel(t, title="[bold]Basic Info[/]", border_style="blue", padding=(1, 2)))
            input("\nPress Enter to continue...")

        elif choice == "2":
            clear_screen()
            size = server.get("size", {})
            opts = server.get("selected_size_options", {})
            items = [
                ("Memory:", f"{server.get('memory')} MB"),
                ("vCPUs:", str(server.get("vcpus", ""))),
                ("Disk:", f"{server.get('disk')} GB"),
                ("Size Slug:", server.get("size_slug", "")),
            ]
            size_type = size.get("size_type") or {}
            items.append(("Plan Type:", size_type.get("name", "")))
            items.append(("Price Monthly:", f"${size.get('price_monthly')}"))
            items.append(("Price Hourly:", f"${size.get('price_hourly')}"))
            if opts:
                for key, value in opts.items():
                    items.append((f"  {key}:", str(value)))
            t = make_info_table(items)
            console.print(Panel(t, title="[bold]Specifications[/]", border_style="blue", padding=(1, 2)))
            input("\nPress Enter to continue...")

        elif choice == "3":
            clear_screen()
            networks = server.get("networks", {})
            items = [
                ("MAC Address:", networks.get("mac_address", "")),
                ("Port Blocking:", str(networks.get("port_blocking", ""))),
            ]
            for entry in networks.get("v4", []):
                kind = entry.get("type", "unknown")
                ip = entry.get("ip_address", "")
                reverse = entry.get("reverse_name", "")
                items.append((f"IPv4 ({kind}):", f"{ip} ({reverse})"))
            v6 = networks.get("v6", [])
            if v6:
                for entry in v6:
                    kind = entry.get("type", "unknown")
                    items.append((f"IPv6 ({kind}):", entry.get("ip_address", "")))
            else:
                items.append(("IPv6:", "None configured"))
            t = make_info_table(items)
            console.print(Panel(t, title="[bold]Networking[/]", border_style="blue", padding=(1, 2)))
            input("\nPress Enter to continue...")

        elif choice == "4":
            clear_screen()
            region = server.get("region", {})
            image = server.get("image", {})
            t = make_info_table([
                ("Region:", f"{region.get('name')} ({region.get('slug')})"),
                ("Region Available:", str(region.get("available", ""))),
                ("OS:", f"{image.get('full_name')} ({image.get('distribution')})"),
                ("Image Type:", image.get("type", "")),
                ("Image Slug:", image.get("slug", "")),
            ])
            console.print(Panel(t, title="[bold]Region & OS[/]", border_style="blue", padding=(1, 2)))
            input("\nPress Enter to continue...")

        elif choice == "5":
            clear_screen()
            backup_settings = server.get("backup_settings") or {}
            items = [
                ("Backup IDs:", str(server.get("backup_ids", ""))),
                ("Next Backup Window:", str(server.get("next_backup_window", ""))),
            ]
            for key, value in backup_settings.items():
                items.append((f"  {key}:", str(value)))
            items.append(("Under Maintenance:", str(server.get("is_under_maintenance", ""))))
            items.append(("Features:", str(server.get("features", ""))))
            t = make_info_table(items)
            console.print(Panel(t, title="[bold]Backups & Maintenance[/]", border_style="blue", padding=(1, 2)))
            input("\nPress Enter to continue...")

        elif choice == "6":
            clear_screen()
            console.print(Panel("", title="[bold]Full JSON[/]", border_style="blue", padding=(1, 2)))
            print_json(data)
            input("\nPress Enter to continue...")

        elif choice == "7":
            show_performance_menu(client, server_id)

        elif choice == "8":
            break

        else:
            console.print("[red]Invalid option. Press Enter to continue...[/]")
            input()


def format_kbps(kbps: float) -> str:
    """Convert Kbps to human-readable string."""
    if kbps >= 1000:
        return f"{kbps/1000:.2f} Mbps"
    return f"{kbps:.2f} Kbps"


def format_bytes_to_mb(bytes_val: float) -> str:
    """Convert bytes to MB."""
    return f"{bytes_val / (1024*1024):.2f} MB"


def format_bytes_to_gb(bytes_val: float) -> str:
    """Convert bytes to GB."""
    return f"{bytes_val / (1024*1024*1024):.2f} GB"


def show_performance_menu(client: BinaryLaneClient, server_id: int):
    while True:
        clear_screen()
        table = Table(show_header=False, box=box.SIMPLE, padding=(0, 2))
        table.add_column(style="cyan", justify="right", width=2)
        table.add_column("")
        table.add_row("1.", "Data Transfer (bandwidth this period)")
        table.add_row("2.", "Current Performance (CPU, RAM, I/O)")
        table.add_row("3.", "Back to Server Menu")
        panel = Panel(
            table,
            title="[bold yellow]Performance & Usage[/]",
            border_style="blue",
            padding=(1, 2),
        )
        console.print(panel)

        choice = input("Select an option: ").strip()

        if choice == "1":
            clear_screen()
            try:
                data = client.get_data_usage(server_id)
                du = data.get("data_usage", {})
                if not du:
                    console.print("[yellow]No data usage information available.[/]")
                else:
                    total_gb = du.get("transfer_gigabytes", 0)
                    used_gb = du.get("current_transfer_usage_gigabytes", 0)
                    percent = (used_gb / total_gb * 100) if total_gb > 0 else 0
                    period_end = du.get("transfer_period_end", "N/A")
                    expires = du.get("expires", "N/A")

                    bar = Progress(
                        TextColumn(""),
                        BarColumn(),
                        TextColumn("{task.percentage:.1f}%"),
                        console=console,
                    )
                    bar.add_task("", total=total_gb, completed=used_gb)

                    items = [
                        ("Included Transfer:", f"{total_gb} GB"),
                        ("Used:", f"{used_gb:.3f} GB"),
                    ]
                    if used_gb > total_gb:
                        excess = used_gb - total_gb
                        items.append(("EXCESS:", f"[red]{excess:.3f} GB (overage charges apply)[/]"))
                    else:
                        remaining = total_gb - used_gb
                        items.append(("Remaining:", f"{remaining:.3f} GB"))
                    items.append(("Period Ends:", period_end))
                    items.append(("Expires:", expires))

                    info_table = make_info_table(items)
                    content = Table.grid(padding=(0, 0))
                    content.add_row(info_table)
                    content.add_row(Panel(bar, border_style="green"))
                    console.print(Panel(content, title="[bold]Data Transfer[/]", border_style="blue", padding=(1, 2)))
            except BinaryLaneAPIError as e:
                console.print(f"[red]Error:[/] {e}")
            input("\nPress Enter to continue...")

        elif choice == "2":
            clear_screen()
            try:
                data = client.get_latest_sample_set(
                    server_id, data_interval="five-minute"
                )
                ss = data.get("sample_set")
                if not ss:
                    console.print("[yellow]No performance sample data available.[/]")
                else:
                    avg = ss.get("average", {})
                    period = ss.get("period", {})
                    max_mem_mb = ss.get("maximum_memory_megabytes", 0)
                    max_storage_gb = ss.get("maximum_storage_gigabytes", 0)

                    cpu = avg.get("cpu_usage_percent", 0)
                    cpu_detailed = avg.get("cpu_usage_detailed", [])
                    mem_bytes = avg.get("memory_usage_bytes", 0)
                    net_in = avg.get("network_incoming_kbps", 0)
                    net_out = avg.get("network_outgoing_kbps", 0)
                    storage_used_mb = avg.get("storage_usage_megabytes", 0)
                    storage_read_kbps = avg.get("storage_read_kbps", 0)
                    storage_write_kbps = avg.get("storage_write_kbps", 0)
                    read_iops = avg.get("storage_read_requests_per_second", 0)
                    write_iops = avg.get("storage_write_requests_per_second", 0)

                    cpu_bar = Progress(
                        TextColumn(""),
                        BarColumn(),
                        TextColumn(f"{{task.percentage:.1f}}%"),
                        console=console,
                    )
                    cpu_bar.add_task("CPU", total=100, completed=cpu)

                    items = [
                        ("Period:", f"{period.get('start', '?')} to {period.get('end', '?')}"),
                        ("Interval:", period.get("data_interval", "?")),
                    ]
                    info_table = make_info_table(items)
                    perf_items = [
                        ("Memory:", f"{format_bytes_to_mb(mem_bytes)} avg | {max_mem_mb:.2f} MB peak"),
                        ("Network:", f"{format_kbps(net_in)} in | {format_kbps(net_out)} out"),
                        ("Storage:", f"{storage_used_mb:.2f} MB used"),
                        ("Read:", f"{format_kbps(storage_read_kbps)} | {read_iops:.1f} IOPS"),
                        ("Write:", f"{format_kbps(storage_write_kbps)} | {write_iops:.1f} IOPS"),
                        ("Peak Storage:", f"{max_storage_gb:.2f} GB"),
                    ]
                    if cpu_detailed:
                        cores = " | ".join(
                            [f"v{i+1}: {c:.1f}%" for i, c in enumerate(cpu_detailed)]
                        )
                        perf_items.insert(0, ("Per-core:", cores))
                    perf_table = make_info_table(perf_items)

                    content = Table.grid(padding=(0, 0))
                    content.add_row(info_table)
                    content.add_row(Panel(cpu_bar, border_style="green"))
                    content.add_row(perf_table)
                    console.print(Panel(content, title="[bold]Current Performance[/]", border_style="blue", padding=(1, 2)))
            except BinaryLaneAPIError as e:
                console.print(f"[red]Error:[/] {e}")
            input("\nPress Enter to continue...")

        elif choice == "3":
            break

        else:
            console.print("[red]Invalid option. Press Enter to continue...[/]")
            input()


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

    elif choice.lower() == "q":
        clear_screen()
        console.print("[bold green]Goodbye![/]")
        sys.exit(0)

    else:
        clear_screen()
        console.print("[red]Invalid option. Press Enter to continue...[/]")
        input()


def main():
    load_dotenv()

    token = os.environ.get("API_TOKEN")
    if not token:
        print("Error: API_TOKEN not found in environment.")
        sys.exit(1)

    client = BinaryLaneClient(token)

    while True:
        show_main_menu()
        choice = input("Select an option: ").strip()
        run_main_choice(client, choice)


if __name__ == "__main__":
    main()
