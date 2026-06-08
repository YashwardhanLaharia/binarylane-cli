import os
import sys
import json

import requests
from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich import box

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
    print(json.dumps(data, indent=2))


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
        title="[bold yellow]BinaryLane API Explorer[/]",
        border_style="blue",
        padding=(1, 2),
    )
    console.print(panel)


def show_servers_menu(client: BinaryLaneClient):
    clear_screen()
    print("=" * 50)
    print("Your Servers")
    print("=" * 50)

    try:
        servers = client.get_server_list()
    except BinaryLaneAPIError as e:
        print(f"Error: {e}")
        prompt_choice()
        return

    if not servers:
        print("No servers found.")
        prompt_choice()
        return

    for i, server in enumerate(servers, 1):
        region = server.get("region", {})
        image = server.get("image", {})
        name = server.get("name", "Unknown")
        sid = server.get("id", "?")
        status = server.get("status", "unknown")
        region_name = region.get("slug", "?")
        os_name = image.get("distribution", "?")
        os_version = image.get("name", "")
        os_full = f"{os_name} {os_version}".strip()
        print(
            f"{i}) {name:30s} (ID: {sid:<8d}) [{status:8s}] {region_name:<8s} {os_full}"
        )

    print("=" * 50)
    print("0) Back to Main Menu")
    print("=" * 50)

    choice = input("Select a server by index: ").strip()

    if choice == "0":
        return

    try:
        idx = int(choice)
        if 1 <= idx <= len(servers):
            server_id = servers[idx - 1]["id"]
            show_server_details_menu(client, server_id)
        else:
            print("Error: Invalid index.")
            prompt_choice()
    except ValueError:
        print("Error: Please enter a number.")
        prompt_choice()


def show_server_details_menu(client: BinaryLaneClient, server_id: int):
    try:
        data = client.get_server(server_id)
    except BinaryLaneAPIError as e:
        print(f"Error fetching server details: {e}")
        prompt_choice()
        return

    server = data.get("server", {})
    if not server:
        print("No server data returned.")
        prompt_choice()
        return

    while True:
        clear_screen()
        print("=" * 50)
        print(f"Server: {server.get('name', 'Unknown')}")
        print("=" * 50)
        print("1. Basic Info")
        print("2. Specifications")
        print("3. Networking")
        print("4. Region & Operating System")
        print("5. Backups & Maintenance")
        print("6. Full JSON")
        print("7. Performance & Usage")
        print("8. Back to Main Menu")
        print("=" * 50)

        choice = input("Select an option: ").strip()

        if choice == "1":
            clear_screen()
            print("=" * 50)
            print("Basic Info")
            print("=" * 50)
            print(f"ID: {server.get('id')}")
            print(f"Hostname: {server.get('name')}")
            print(f"Status: {server.get('status')}")
            print(f"Created At: {server.get('created_at')}")
            print(f"Permalink: {server.get('permalink')}")
            print(
                f"Password Change Supported: {server.get('password_change_supported')}"
            )
            input("\nPress Enter to continue...")

        elif choice == "2":
            clear_screen()
            print("=" * 50)
            print("Specifications")
            print("=" * 50)
            size = server.get("size", {})
            opts = server.get("selected_size_options", {})
            print(f"Memory: {server.get('memory')} MB")
            print(f"vCPUs: {server.get('vcpus')}")
            print(f"Disk: {server.get('disk')} GB")
            print(f"Size Slug: {server.get('size_slug')}")
            size_type = size.get("size_type") or {}
            print(f"Plan Type: {size_type.get('name')}")
            print(f"Price Monthly: ${size.get('price_monthly')}")
            print(f"Price Hourly: ${size.get('price_hourly')}")
            if opts:
                print("\nSelected Options:")
                for key, value in opts.items():
                    print(f"  - {key}: {value}")
            else:
                print("Selected Options: default")
            input("\nPress Enter to continue...")

        elif choice == "3":
            clear_screen()
            print("=" * 50)
            print("Networking")
            print("=" * 50)
            networks = server.get("networks", {})
            print(f"MAC Address: {networks.get('mac_address')}")
            print(f"Port Blocking Enabled: {networks.get('port_blocking')}")

            print("\nIPv4 Addresses:")
            for entry in networks.get("v4", []):
                kind = entry.get("type", "unknown")
                ip = entry.get("ip_address")
                reverse = entry.get("reverse_name")
                print(f"  - {kind}: {ip} (reverse: {reverse})")

            v6_entries = networks.get("v6", [])
            print("\nIPv6 Addresses:")
            if v6_entries:
                for entry in v6_entries:
                    kind = entry.get("type", "unknown")
                    print(f"  - {kind}: {entry.get('ip_address')}")
            else:
                print("  - None configured")
            input("\nPress Enter to continue...")

        elif choice == "4":
            clear_screen()
            print("=" * 50)
            print("Region & Operating System")
            print("=" * 50)
            region = server.get("region", {})
            image = server.get("image", {})
            print(f"Region: {region.get('name')} ({region.get('slug')})")
            print(f"Region Available: {region.get('available')}")
            print(f"OS: {image.get('full_name')} ({image.get('distribution')})")
            print(f"Image Type: {image.get('type')}")
            print(f"Image Slug: {image.get('slug')}")
            input("\nPress Enter to continue...")

        elif choice == "5":
            clear_screen()
            print("=" * 50)
            print("Backups & Maintenance")
            print("=" * 50)
            print(f"Backup IDs: {server.get('backup_ids')}")
            print(f"Next Backup Window: {server.get('next_backup_window')}")
            backup_settings = server.get("backup_settings") or {}
            print("Backup Settings:")
            for key, value in backup_settings.items():
                print(f"  - {key}: {value}")
            print(f"Under Maintenance: {server.get('is_under_maintenance')}")
            print(f"Features: {server.get('features')}")
            input("\nPress Enter to continue...")

        elif choice == "6":
            clear_screen()
            print("=" * 50)
            print("Full JSON")
            print("=" * 50)
            print_json(data)
            input("\nPress Enter to continue...")

        elif choice == "7":
            show_performance_menu(client, server_id)

        elif choice == "8":
            break

        else:
            print("Invalid option. Press Enter to continue...")
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
        print("=" * 50)
        print("Performance & Usage")
        print("=" * 50)
        print("1. Data Transfer (bandwidth this period)")
        print("2. Current Performance (CPU, RAM, I/O)")
        print("3. Back to Server Menu")
        print("=" * 50)

        choice = input("Select an option: ").strip()

        if choice == "1":
            clear_screen()
            print("=" * 50)
            print("Data Transfer")
            print("=" * 50)
            try:
                data = client.get_data_usage(server_id)
                du = data.get("data_usage", {})
                if not du:
                    print("No data usage information available.")
                else:
                    total_gb = du.get("transfer_gigabytes", 0)
                    used_gb = du.get("current_transfer_usage_gigabytes", 0)
                    percent = (used_gb / total_gb * 100) if total_gb > 0 else 0
                    period_end = du.get("transfer_period_end", "N/A")
                    expires = du.get("expires", "N/A")
                    print(f"Included Transfer: {total_gb} GB")
                    print(f"Used: {used_gb:.3f} GB ({percent:.1f}%)")
                    if used_gb > total_gb:
                        excess = used_gb - total_gb
                        print(f"EXCESS: {excess:.3f} GB used (overage charges apply)")
                    else:
                        remaining = total_gb - used_gb
                        print(f"Remaining: {remaining:.3f} GB")
                    print(f"Period Ends: {period_end}")
                    print(f"Expires: {expires}")
            except BinaryLaneAPIError as e:
                print(f"Error: {e}")
            input("\nPress Enter to continue...")

        elif choice == "2":
            clear_screen()
            print("=" * 50)
            print("Current Performance")
            print("=" * 50)
            try:
                data = client.get_latest_sample_set(
                    server_id, data_interval="five-minute"
                )
                ss = data.get("sample_set")
                if not ss:
                    print("No performance sample data available.")
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

                    print(
                        f"Period: {period.get('start', '?')} to {period.get('end', '?')}"
                    )
                    print(f"Data Interval: {period.get('data_interval', '?')}")
                    print()
                    print(f"CPU Usage: {cpu:.1f}%")
                    if cpu_detailed:
                        cores = ", ".join(
                            [f"v{i+1}: {c:.1f}%" for i, c in enumerate(cpu_detailed)]
                        )
                        print(f"  Per-core: {cores}")
                    print(
                        f"Memory: {format_bytes_to_mb(mem_bytes)} avg | {max_mem_mb:.2f} MB peak"
                    )
                    print(
                        f"Network: {format_kbps(net_in)} in | {format_kbps(net_out)} out"
                    )
                    print(f"Storage: {storage_used_mb:.2f} MB used")
                    print(
                        f"  Read:  {format_kbps(storage_read_kbps)} | {read_iops:.1f} IOPS"
                    )
                    print(
                        f"  Write: {format_kbps(storage_write_kbps)} | {write_iops:.1f} IOPS"
                    )
                    print(f"Peak Storage: {max_storage_gb:.2f} GB")
            except BinaryLaneAPIError as e:
                print(f"Error: {e}")
            input("\nPress Enter to continue...")

        elif choice == "3":
            break

        else:
            print("Invalid option. Press Enter to continue...")
            input()


def run_main_choice(client: BinaryLaneClient, choice: str):
    if choice == "1":
        clear_screen()
        print("=" * 50)
        print("Account Info")
        print("=" * 50)
        try:
            data = client.get_account()
            print_json(data)
        except BinaryLaneAPIError as e:
            print(f"Error: {e}")
        prompt_choice()

    elif choice == "2":
        show_servers_menu(client)

    elif choice == "3":
        clear_screen()
        print("=" * 50)
        print("List Recent Actions")
        print("=" * 50)
        try:
            data = client.list_actions()
            print_json(data)
        except BinaryLaneAPIError as e:
            print(f"Error: {e}")
        prompt_choice()

    elif choice == "4":
        clear_screen()
        print("=" * 50)
        print("Perform Server Action")
        print("=" * 50)

        # Reuse the server picker
        try:
            servers = client.get_server_list()
        except BinaryLaneAPIError as e:
            print(f"Error: {e}")
            prompt_choice()
            return

        if not servers:
            print("No servers found.")
            prompt_choice()
            return

        for i, server in enumerate(servers, 1):
            print(f"{i}) {server['name']} (ID: {server['id']})")
        print("0) Cancel")

        s_choice = input("Select a server by index: ").strip()
        if s_choice == "0":
            return

        try:
            idx = int(s_choice)
            if not (1 <= idx <= len(servers)):
                print("Error: Invalid index.")
                prompt_choice()
                return
            server_id = servers[idx - 1]["id"]
        except ValueError:
            print("Error: Please enter a number.")
            prompt_choice()
            return

        clear_screen()
        print("=" * 50)
        print(f"Perform Action on Server (ID: {server_id})")
        print("=" * 50)
        action_type = input(
            "Enter action type (e.g., reboot, power_on, power_off): "
        ).strip()
        if not action_type:
            print("Error: Action type required.")
            prompt_choice()
            return
        try:
            data = client.perform_server_action(server_id, action_type)
            print_json(data)
        except BinaryLaneValidationError as e:
            print(f"Validation error: {e}")
            if e.response_data:
                print(e.response_data)
        except BinaryLaneAPIError as e:
            print(f"Error: {e}")
        prompt_choice()

    elif choice.lower() == "q":
        clear_screen()
        print("Goodbye!")
        sys.exit(0)

    else:
        clear_screen()
        print("Invalid option. Press Enter to continue...")
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
