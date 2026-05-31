from __future__ import annotations

import argparse
import logging
import os
import platform
import socket
import subprocess
import sys
import time
import webbrowser
from pathlib import Path

from backend.app import create_app


BASE_DIR = Path(__file__).resolve().parent
LOG_DIR = BASE_DIR / "logs"


def dashboard_url(host: str, port: int) -> str:
    browser_host = "127.0.0.1" if host in {"0.0.0.0", "::"} else host
    return f"http://{browser_host}:{port}"


def port_is_open(host: str, port: int) -> bool:
    probe_host = "127.0.0.1" if host in {"0.0.0.0", "::"} else host
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(0.3)
            return sock.connect_ex((probe_host, port)) == 0
    except PermissionError as error:
        raise RuntimeError("Local socket checks are blocked in this terminal") from error


def run_dashboard(args: argparse.Namespace) -> int:
    url = dashboard_url(args.host, args.port)
    try:
        dashboard_running = port_is_open(args.host, args.port)
    except RuntimeError:
        dashboard_running = False
    if dashboard_running:
        print("USBSHADOW dashboard is already running.")
        print(f"Open: {url}")
        print(f"Use another port with: python usbshadow.py dashboard --port {args.port + 1}")
        return 0

    print("Starting USBSHADOW dashboard...")
    print(f"Open: {url}")
    app = create_app()
    if not args.debug:
        from waitress import serve

        print("Running with Waitress production WSGI server.")
        try:
            serve(app, host=args.host, port=args.port)
        except PermissionError as error:
            print(f"Could not bind to {args.host}:{args.port}: {error}")
            return 2
        except OSError as error:
            print(f"Could not start dashboard on {args.host}:{args.port}: {error}")
            return 2
        return 0

    print("Running Flask debug server. Press Ctrl+C to stop.")
    try:
        app.run(host=args.host, port=args.port, debug=args.debug)
    except PermissionError as error:
        print(f"Could not bind to {args.host}:{args.port}: {error}")
        print("Try a different port or run from a terminal with permission to bind local sockets.")
        return 2
    except OSError as error:
        print(f"Could not start dashboard on {args.host}:{args.port}: {error}")
        return 2
    return 0


def run_agent(args: argparse.Namespace) -> int:
    system = (args.platform or platform.system()).lower()
    logging.basicConfig(level=getattr(logging, args.log_level.upper(), logging.INFO))
    api_url = os.getenv("USBSHADOW_API", "http://127.0.0.1:5000")
    print(f"Starting USBSHADOW {system} USB agent.")
    print(f"Sending events to: {api_url}")
    print("Keep this terminal open. Press Ctrl+C to stop monitoring.")
    if system == "windows":
        from agent.windows_monitor import run
    elif system == "linux":
        from agent.linux_monitor import run
    elif system in {"darwin", "macos", "mac"}:
        from agent.mac_monitor import run
    else:
        raise SystemExit(f"Unsupported platform: {system}")
    try:
        run()
    except KeyboardInterrupt:
        print("\nUSBSHADOW agent stopped.")
    return 0


def run_file_watch(args: argparse.Namespace) -> int:
    from agent.file_monitor import run_forever

    path = Path(args.path).expanduser()
    if str(path).startswith("/path/to/"):
        print("Replace the example path with your real USB mount path.")
        print("Linux example: python usbshadow.py file-watch /media/$USER/USB")
        print("macOS example: python usbshadow.py file-watch /Volumes/USB")
        return 2
    if not path.exists() or not path.is_dir():
        print(f"USB path does not exist or is not a directory: {path}")
        print("Plug in the USB device, find its mount path, then run file-watch again.")
        return 2

    logging.basicConfig(level=getattr(logging, args.log_level.upper(), logging.INFO))
    print(f"Watching file activity under: {path}")
    print("Keep this terminal open. Press Ctrl+C to stop watching.")
    try:
        run_forever(str(path), device_id=args.device_id)
    except KeyboardInterrupt:
        print("\nUSBSHADOW file watcher stopped.")
    return 0


def run_status(args: argparse.Namespace) -> int:
    url = dashboard_url(args.host, args.port)
    try:
        dashboard_running = port_is_open(args.host, args.port)
    except RuntimeError:
        print("Dashboard status cannot be checked from this restricted terminal.")
        print(f"Try opening: {url}")
        return 2
    if dashboard_running:
        print("Dashboard: online")
        print(f"Open: {url}")
        return 0
    print("Dashboard: offline")
    print(f"Start it with: python usbshadow.py dashboard --port {args.port}")
    return 1


def run_open(args: argparse.Namespace) -> int:
    url = dashboard_url(args.host, args.port)
    try:
        dashboard_running = port_is_open(args.host, args.port)
    except RuntimeError:
        dashboard_running = False

    if not dashboard_running:
        LOG_DIR.mkdir(exist_ok=True)
        log_file = LOG_DIR / "dashboard-background.log"
        with log_file.open("ab") as handle:
            subprocess.Popen(
                [
                    sys.executable,
                    str(BASE_DIR / "usbshadow.py"),
                    "dashboard",
                    "--host",
                    args.host,
                    "--port",
                    str(args.port),
                ],
                cwd=str(BASE_DIR),
                stdout=handle,
                stderr=handle,
                start_new_session=True,
            )
        time.sleep(1.5)

    print(f"Opening USBSHADOW dashboard: {url}")
    opened = webbrowser.open(url)
    if not opened:
        print(f"Open this URL in your browser: {url}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="usbshadow",
        description="USBSHADOW USB forensics dashboard and monitoring agent.",
    )
    subcommands = parser.add_subparsers(dest="command", required=True)

    dashboard = subcommands.add_parser("dashboard", help="Start the web GUI dashboard")
    dashboard.add_argument("--host", default="127.0.0.1")
    dashboard.add_argument("--port", type=int, default=5000)
    dashboard.add_argument("--debug", action="store_true", help="Use Flask debug server")
    dashboard.set_defaults(func=run_dashboard)

    status = subcommands.add_parser("status", help="Check whether the dashboard is running")
    status.add_argument("--host", default="127.0.0.1")
    status.add_argument("--port", type=int, default=5000)
    status.set_defaults(func=run_status)

    open_dashboard = subcommands.add_parser(
        "open", help="Open the dashboard, starting it in the background if needed"
    )
    open_dashboard.add_argument("--host", default="127.0.0.1")
    open_dashboard.add_argument("--port", type=int, default=5000)
    open_dashboard.set_defaults(func=run_open)

    agent = subcommands.add_parser("agent", help="Start the platform USB monitor")
    agent.add_argument(
        "--platform",
        choices=["windows", "linux", "macos"],
        help="Override automatic platform detection",
    )
    agent.add_argument("--log-level", default="INFO")
    agent.set_defaults(func=run_agent)

    file_watch = subcommands.add_parser(
        "file-watch", help="Watch a mounted USB path for file activity"
    )
    file_watch.add_argument("path")
    file_watch.add_argument("--device-id", type=int)
    file_watch.add_argument("--log-level", default="INFO")
    file_watch.set_defaults(func=run_file_watch)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
