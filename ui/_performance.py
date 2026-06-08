from rich.panel import Panel
from rich.progress import Progress, BarColumn, TextColumn
from rich.table import Table
from rich import box

from client import BinaryLaneClient, BinaryLaneAPIError
from ui._components import (
    clear_screen,
    console,
    make_info_table,
    format_kbps,
)


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
                    period_end = du.get("transfer_period_end", "N/A")
                    expires = du.get("expires", "N/A")

                    bar = Progress(
                        TextColumn("{task.description:16}"),
                        BarColumn(),
                        TextColumn("{task.percentage:.1f}%  ({task.completed:.1f}/{task.total:.1f} GB)"),
                        console=console,
                    )
                    bar.add_task("Data Transfer", total=total_gb, completed=used_gb)

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
                    storage_used_mb = avg.get("storage_usage_megabytes", 0)
                    net_in = avg.get("network_incoming_kbps", 0)
                    net_out = avg.get("network_outgoing_kbps", 0)
                    storage_read_kbps = avg.get("storage_read_kbps", 0)
                    storage_write_kbps = avg.get("storage_write_kbps", 0)
                    read_iops = avg.get("storage_read_requests_per_second", 0)
                    write_iops = avg.get("storage_write_requests_per_second", 0)

                    perf_bar = Progress(
                        TextColumn("{task.description:12}"),
                        BarColumn(),
                        TextColumn("{task.percentage:.1f}%  ({task.completed:.1f}/{task.total:.0f})"),
                        console=console,
                    )
                    perf_bar.add_task("CPU", total=100, completed=cpu)
                    perf_bar.add_task("Memory", total=max_mem_mb, completed=mem_bytes / (1024*1024))
                    perf_bar.add_task("Storage", total=max_storage_gb * 1024, completed=storage_used_mb)

                    items = [
                        ("Period:", f"{period.get('start', '?')} to {period.get('end', '?')}"),
                        ("Interval:", period.get("data_interval", "?")),
                    ]
                    info_table = make_info_table(items)
                    perf_items = [
                        ("Network:", f"{format_kbps(net_in)} in | {format_kbps(net_out)} out"),
                        ("Read:", f"{format_kbps(storage_read_kbps)} | {read_iops:.1f} IOPS"),
                        ("Write:", f"{format_kbps(storage_write_kbps)} | {write_iops:.1f} IOPS"),
                    ]
                    if cpu_detailed:
                        cores = " | ".join(
                            [f"v{i+1}: {c:.1f}%" for i, c in enumerate(cpu_detailed)]
                        )
                        perf_items.insert(0, ("Per-core:", cores))
                    perf_table = make_info_table(perf_items)

                    content = Table.grid(padding=(0, 0))
                    content.add_row(info_table)
                    content.add_row(Panel(perf_bar, border_style="green"))
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