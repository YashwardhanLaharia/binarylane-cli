# BinaryLane CLI

A lightweight, interactive terminal-based interface (TUI) to manage your BinaryLane servers and monitor performance via the [BinaryLane API](https://api.binarylane.com.au/reference).

## Features

- **Account Information:** View your account configuration (name, email, UUID, status).
- **Server Management:** List all servers, view detailed specs, network config, region, OS, and backups.
- **Server Actions:** Perform reboots, power-ons, and power-offs directly from the terminal.
- **Performance & Usage:** Monitor real-time CPU, RAM, disk I/O, data transfer usage, and network throughput.
- **Speedtest (Local to VPS):** Ping each server's public IPv4 and display latency, packet loss, and VPS-side network in/out metrics.

## Prerequisites

- Python 3.8+
- A BinaryLane API token (generate one from your [BinaryLane dashboard](https://www.binarylane.com.au/))

## Setup

```bash
# Clone the repository
git clone https://github.com/YashwardhanLaharia/binarylane-cli.git
cd binarylane-cli

# Create and activate a virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure your API token
cp .env.example .env
# Edit .env and set your API_TOKEN
```

## Usage

```bash
python3 bl_cli.py
```

The main menu offers the following options:

| Option | Description |
| - | - |
| 1 | Account Info — view your BinaryLane account details |
| 2 | Servers — list servers, view details, and monitor performance |
| 3 | List Recent Actions — view recent API action history |
| 4 | Perform Server Action — reboot, power on/off a server |
| 5 | Speedtest (Local to VPS) — ping each server and display latency + network metrics |
| Q | Quit |

Each server submenu provides access to basic info, specifications, networking (IPv4/IPv6, MAC, reverse DNS), region & OS, backups, full JSON output, and performance monitoring.

## Project Structure

```plaintext
binarylane-cli/
├── bl_cli.py            # Entry point — main CLI loop
├── client.py            # BinaryLane API client
├── requirements.txt     # Python dependencies
├── .env                 # API token (not committed)
├── .env.example         # API token template
└── ui/
    ├── __init__.py
    ├── _components.py   # Shared UI helpers (tables, panels, formatting)
    ├── _main_menu.py    # Main menu and choice routing
    ├── _performance.py  # Data transfer and live performance views
    ├── _server_details.py  # Per-server submenu views
    ├── _server_list.py  # Server list display and selection
    └── _speedtest.py    # Speedtest (ping + sample metrics)
```

## Dependencies

- [requests](https://pypi.org/project/requests/) — HTTP client
- [python-dotenv](https://pypi.org/project/python-dotenv/) — environment variable loading
- [rich](https://pypi.org/project/rich/) — terminal UI framework

## AI Acknowledgement

Parts of this codebase were developed with assistance from AI coding tools.
