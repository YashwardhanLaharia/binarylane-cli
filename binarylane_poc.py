import os
import sys
import json

import requests
from dotenv import load_dotenv

BASE_URL = "https://api.binarylane.com.au"


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


def pretty_print(data):
    print(json.dumps(data, indent=2))


def main():
    load_dotenv()

    print("=" * 50)
    print("1. Account Info")
    print("=" * 50)
    try:
        account = get_account_info()
        pretty_print(account)
    except requests.exceptions.HTTPError as e:
        print(f"Error fetching account info: {e}")

    print("\n" + "=" * 50)
    print("2. List Servers")
    print("=" * 50)
    try:
        servers = list_servers()
        pretty_print(servers)
    except requests.exceptions.HTTPError as e:
        print(f"Error listing servers: {e}")

    # If there are servers, fetch details for the first one
    server_list = servers.get("servers", [])
    if server_list:
        first_server_id = server_list[0]["id"]
        print("\n" + "=" * 50)
        print(f"3. Server Details (ID: {first_server_id})")
        print("=" * 50)
        try:
            server = get_server(first_server_id)
            pretty_print(server)
        except requests.exceptions.HTTPError as e:
            print(f"Error fetching server details: {e}")
    else:
        print("\nNo servers found, skipping server details.")

    print("\n" + "=" * 50)
    print("4. List Recent Actions")
    print("=" * 50)
    try:
        actions = list_actions()
        pretty_print(actions)
    except requests.exceptions.HTTPError as e:
        print(f"Error listing actions: {e}")


if __name__ == "__main__":
    main()
