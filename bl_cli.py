import os
import sys

from dotenv import load_dotenv

from client import BinaryLaneClient
from ui import clear_screen, console, show_main_menu, run_main_choice


def main():
    load_dotenv()

    token = os.environ.get("API_TOKEN")
    if not token:
        print("Error: API_TOKEN not found in environment.")
        sys.exit(1)

    client = BinaryLaneClient(token)

    try:
        while True:
            show_main_menu()
            choice = input("Select an option: ").strip()
            run_main_choice(client, choice)
    except KeyboardInterrupt:
        clear_screen()
        console.print("[bold green]Goodbye![/]")
        sys.exit(0)


if __name__ == "__main__":
    main()