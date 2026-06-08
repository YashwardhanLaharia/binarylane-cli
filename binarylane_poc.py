import os
import sys
import json

import requests
from dotenv import load_dotenv

BASE_URL = "https://api.binarylane.com.au"


def clear_screen():
    os.system("cls" if os.name == "nt" else "clear")


def get_headers():
    token = os.environ.get("API_TOKEN")
    if not token:
        print("Error: API_TOKEN not found in environment.")
        sys.exit(1)
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }


def get_account_info():
    url = f"{BASE_URL}/v2/account"
    response = requests.get(url, headers=get_headers())
    response.raise_for_status()
    return response.json()


def list_servers(page=1, per_page=20):
    url = f"{BASE_URL}/v2/servers"
    params = {"page": page, "per_page": per_page}
    response = requests.get(url, headers=get_headers(), params=params)
    response.raise_for_status()
    return response.json()


def get_server(server_id: int):
    url = f"{BASE_URL}/v2/servers/{server_id}"
    response = requests.get(url, headers=get_headers())
    response.raise_for_status()
    return response.json()


def list_actions(page=1, per_page=20):
    url = f"{BASE_URL}/v2/actions"
    params = {"page": page, "per_page": per_page}
    response = requests.get(url, headers=get_headers(), params=params)
    response.raise_for_status()
    return response.json()


def select_server():
    clear_screen()
    print("=" * 50)
    print("Select a Server")
    print("=" * 50)
    try:
        data = list_servers()
        servers = data.get("servers", [])
        if not servers:
            print("No servers found.")
            return None
        for i, server in enumerate(servers, 1):
            print(f"{i}) {server['name']} (ID: {server['id']})")
        print("=" * 50)
        choice = input("Select a server by index: ").strip()
        try:
            idx = int(choice)
            if 1 <= idx <= len(servers):
                return servers[idx - 1]["id"]
            else:
                print("Error: Invalid index.")
        except ValueError:
            print("Error: Please enter a number.")
    except requests.exceptions.HTTPError as e:
        print(f"Error fetching servers: {e}")
    return None


def perform_server_action(server_id: int, action_type: str, **kwargs):
    url = f"{BASE_URL}/v2/servers/{server_id}/actions"
    payload = {"type": action_type, **kwargs}
    response = requests.post(url, headers=get_headers(), json=payload)
    response.raise_for_status()
    return response.json()


def prompt_action_type():
    return input("Enter action type (e.g., reboot, power_on, power_off): ").strip()


def prompt_choice():
    return input("\nPress Enter to return to menu...")


def show_menu():
    clear_screen()
    print("=" * 50)
    print("BinaryLane API Explorer")
    print("=" * 50)
    print("1. Account Info")
    print("2. List Servers")
    print("3. Server Details")
    print("4. List Recent Actions")
    print("5. Perform Server Action")
    print("Q. Quit")
    print("=" * 50)


def show_server_details_menu(server_data):
    server = server_data.get("server", {})
    if not server:
        print("No server data returned.")
        input("\nPress Enter to continue...")
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
        print("7. Back to Main Menu")
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
            print(f"Password Change Supported: {server.get('password_change_supported')}")
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
            size_type = size.get('size_type') or {}
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
            backup_settings = server.get('backup_settings') or {}
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
            print(json.dumps(server_data, indent=2))
            input("\nPress Enter to continue...")

        elif choice == "7":
            break

        else:
            print("Invalid option. Press Enter to continue...")
            input()


def run_choice(choice):
    if choice == "1":
        clear_screen()
        print("=" * 50)
        print("Account Info")
        print("=" * 50)
        try:
            data = get_account_info()
            print(json.dumps(data, indent=2))
        except requests.exceptions.HTTPError as e:
            print(f"Error: {e}")
        prompt_choice()

    elif choice == "2":
        clear_screen()
        print("=" * 50)
        print("List Servers")
        print("=" * 50)
        try:
            data = list_servers()
            print(json.dumps(data, indent=2))
        except requests.exceptions.HTTPError as e:
            print(f"Error: {e}")
        prompt_choice()

    elif choice == "3":
        server_id = select_server()
        if server_id is None:
            prompt_choice()
            return
        try:
            data = get_server(server_id)
        except requests.exceptions.HTTPError as e:
            print(f"Error fetching server details: {e}")
            prompt_choice()
            return
        show_server_details_menu(data)

    elif choice == "4":
        clear_screen()
        print("=" * 50)
        print("List Recent Actions")
        print("=" * 50)
        try:
            data = list_actions()
            print(json.dumps(data, indent=2))
        except requests.exceptions.HTTPError as e:
            print(f"Error: {e}")
        prompt_choice()

    elif choice == "5":
        clear_screen()
        print("=" * 50)
        print("Perform Server Action")
        print("=" * 50)
        server_id = select_server()
        if server_id is None:
            prompt_choice()
            return
        clear_screen()
        print("=" * 50)
        print(f"Perform Action on Server (ID: {server_id})")
        print("=" * 50)
        action_type = prompt_action_type()
        if not action_type:
            print("Error: Action type required.")
            prompt_choice()
            return
        try:
            data = perform_server_action(server_id, action_type)
            print(json.dumps(data, indent=2))
        except requests.exceptions.HTTPError as e:
            print(f"Error performing action: {e}")
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
    while True:
        show_menu()
        choice = input("Select an option: ").strip()
        run_choice(choice)


if __name__ == "__main__":
    main()
