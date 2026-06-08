import re
import subprocess
import platform
from typing import Optional

from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich import box

from client import BinaryLaneClient, BinaryLaneAPIError
from ui._components import clear_screen, console, prompt_choice, format_kbps


def _ping_latency(host: str, count: int = 4) -> dict:
    try:
        result = subprocess.run(
            ["ping", "-c", str(count), host],
            capture_output=True,
            text=True,
            timeout=30,
        )
    except subprocess.TimeoutExpired:
        return {"error": "Timed out"}
    except FileNotFoundError:
        return {"error": "ping not found"}

    stdout = result.stdout

    loss_match = re.search(r"(\d+)% packet loss", stdout)
    packet_loss = int(loss_match.group(1)) if loss_match else 100

    rtt_match = re.search(
        r"rtt min/avg/max/mdev\s*=\s*([\d.]+)/([\d.]+)/([\d.]+)/([\d.]+)\s*ms",
        stdout,
    )
    if rtt_match:
        return {
            "min": float(rtt_match.group(1)),
            "avg": float(rtt_match.group(2)),
            "max": float(rtt_match.group(3)),
            "mdev": float(rtt_match.group(4)),
            "loss": packet_loss,
        }

    if result.returncode != 0:
        return {"error": "Unreachable", "loss": packet_loss}

    return {"error": "Could not parse ping output", "loss": packet_loss}


def _latency_verdict(avg: float) -> str:
    if avg < 20:
        return "[green]Excellent[/]"
    if avg < 50:
        return "[cyan]Good[/]"
    if avg < 100:
        return "[yellow]Fair[/]"
    if avg < 200:
        return "[orange1]Poor[/]"
    return "[red]Bad[/]"


def _get_public_ipv4(server: dict) -> str | None:
    networks = server.get("networks", {})
    for entry in networks.get("v4", []):
        if entry.get("type") == "public" and entry.get("ip_address"):
            return entry["ip_address"]
    return None


def run_speedtest(client: BinaryLaneClient):
    clear_screen()

    try:
        servers = client.get_server_list()
    except BinaryLaneAPIError as e:
        console.print(f"[red]Error fetching servers:[/] {e}")
        prompt_choice()
        return

    if not servers:
        console.print("[yellow]No servers found.[/]")
        prompt_choice()
        return

    console.print(Panel("[bold]Testing connectivity to your VPS servers...[/]", border_style="blue", padding=(1, 2)))

    table = Table(box=box.SIMPLE, padding=(0, 1))
    table.add_column("Server", style="cyan")
    table.add_column("Public IPv4", style="white")
    table.add_column("Latency (min/avg/max)", justify="center")
    table.add_column("Packet Loss", justify="center")
    table.add_column("VPS Network In", justify="center")
    table.add_column("VPS Network Out", justify="center")
    table.add_column("Verdict", justify="center")

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Running speedtests...", total=len(servers))

        for server in servers:
            sid = server["id"]
            name = server["name"]

            try:
                data = client.get_server(sid)
                full = data.get("server", {})
            except BinaryLaneAPIError:
                table.add_row(name, "[red]API error[/]", "", "", "", "", "")
                progress.advance(task)
                continue

            ip = _get_public_ipv4(full)
            if not ip:
                table.add_row(name, "[dim]No public IP[/]", "", "", "", "", "")
                progress.advance(task)
                continue

            ping_result = _ping_latency(ip)

            try:
                samples = client.get_latest_sample_set(sid)
                net_in = samples.get("network_incoming_kbps", 0)
                net_out = samples.get("network_outgoing_kbps", 0)
                vps_in = format_kbps(net_in)
                vps_out = format_kbps(net_out)
            except BinaryLaneAPIError:
                vps_in = "[dim]N/A[/]"
                vps_out = "[dim]N/A[/]"

            err = ping_result.get("error")
            if err:
                loss = ping_result.get("loss", 100)
                loss_str = f"[red]{loss}%[/]" if loss > 0 else "[green]0%[/]"
                table.add_row(name, ip, f"[red]{err}[/]", loss_str, vps_in, vps_out, "[red]N/A[/]")
            else:
                loss_str = f"[red]{ping_result['loss']}%[/]" if ping_result["loss"] > 0 else "[green]0%[/]"
                latency_str = f"{ping_result['min']:.1f}/{ping_result['avg']:.1f}/{ping_result['max']:.1f} ms"
                verdict = _latency_verdict(ping_result["avg"])
                table.add_row(name, ip, latency_str, loss_str, vps_in, vps_out, verdict)

            progress.advance(task)

    console.print()
    console.print(Panel(table, title="[bold]Speedtest Results[/]", border_style="blue", padding=(1, 2)))
    prompt_choice()