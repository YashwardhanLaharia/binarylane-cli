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


def perform_server_action(server_id: int, action_type: str, **kwargs):
    url = f"{BASE_URL}/v2/servers/{server_id}/actions"
    payload = {"type": action_type, **kwargs}
    response = requests.post(url, headers=get_headers(), json=payload)
    response.raise_for_status()
    return response.json()


def prompt_server_id():
    sid = input("Enter Server ID: ").strip()
    try:
        return int(sid)
    except ValueError:
        print("Error: Server ID must be an integer.")
        return None


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
        clear_screen()
        print("=" * 50)
        print("Server Details")
        print("=" * 50)
        server_id = prompt_server_id()
        if server_id is not None:
            try:
                data = get_server(server_id)
                print(json.dumps(data, indent=2))
            except requests.exceptions.HTTPError as e:
                print(f"Error: {e}")
        prompt_choice()

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
        server_id = prompt_server_id()
        if server_id is not None:
            action_type = prompt_action_type()
            if action_type:
                try:
                    data = perform_server_action(server_id, action_type)
                    print(json.dumps(data, indent=2))
                except requests.exceptions.HTTPError as e:
                    print(f"Error: {e}")
            else:
                print("Error: Action type required.")
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
