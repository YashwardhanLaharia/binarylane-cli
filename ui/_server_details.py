from rich.panel import Panel
from rich.table import Table
from rich import box

from client import BinaryLaneClient, BinaryLaneAPIError
from ui._components import clear_screen, console, make_info_table, print_json
from ui._performance import show_performance_menu


def show_server_details_menu(client: BinaryLaneClient, server_id: int):
    try:
        data = client.get_server(server_id)
    except BinaryLaneAPIError as e:
        console.print(f"[red]Error fetching server details:[/] {e}")
        input("\nPress Enter to continue...")
        return

    server = data.get("server", {})
    if not server:
        console.print("[red]No server data returned.[/]")
        input("\nPress Enter to continue...")
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