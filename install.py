from __future__ import annotations

import argparse
import os
import platform
import shutil
import stat
import subprocess
import sys
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
PYTHON = BASE_DIR / ".venv" / ("Scripts/python.exe" if os.name == "nt" else "bin/python")


def run(command: list[str], check: bool = True) -> subprocess.CompletedProcess:
    print("+", " ".join(command))
    return subprocess.run(command, check=check)


def ensure_venv() -> None:
    if PYTHON.exists():
        return
    run([sys.executable, "-m", "venv", str(BASE_DIR / ".venv")])


def install_dependencies() -> None:
    ensure_venv()
    run([str(PYTHON), "-m", "pip", "install", "-r", str(BASE_DIR / "requirements.txt")])


def ensure_env() -> None:
    env_file = BASE_DIR / ".env"
    if not env_file.exists():
        shutil.copyfile(BASE_DIR / ".env.example", env_file)


def ensure_shell_path(bin_dir: Path) -> None:
    marker = 'export PATH="$HOME/.local/bin:$PATH"'
    if bin_dir != Path.home() / ".local" / "bin":
        return
    for profile_name in (".profile", ".bashrc", ".zshrc"):
        profile = Path.home() / profile_name
        existing = profile.read_text() if profile.exists() else ""
        if marker in existing:
            continue
        with profile.open("a", encoding="utf-8") as handle:
            if existing and not existing.endswith("\n"):
                handle.write("\n")
            handle.write(f"\n# USBSHADOW launcher\n{marker}\n")


def install_linux() -> None:
    service_dir = Path.home() / ".config" / "systemd" / "user"
    service_dir.mkdir(parents=True, exist_ok=True)
    python = str(PYTHON)
    project = str(BASE_DIR)

    dashboard_service = f"""[Unit]
Description=USBSHADOW Dashboard
After=network.target

[Service]
Type=simple
WorkingDirectory={project}
ExecStart={python} {project}/usbshadow.py dashboard --host 127.0.0.1 --port 5000
Restart=on-failure
RestartSec=5
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=default.target
"""

    agent_service = f"""[Unit]
Description=USBSHADOW USB Agent
After=network.target usbshadow-dashboard.service

[Service]
Type=simple
WorkingDirectory={project}
ExecStart={python} {project}/usbshadow.py agent --platform linux
Restart=always
RestartSec=5
Environment=USBSHADOW_API=http://127.0.0.1:5000
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=default.target
"""

    (service_dir / "usbshadow-dashboard.service").write_text(dashboard_service)
    (service_dir / "usbshadow-agent.service").write_text(agent_service)

    bin_dir = Path.home() / ".local" / "bin"
    bin_dir.mkdir(parents=True, exist_ok=True)
    launcher = bin_dir / "usb"
    launcher.write_text(
        f"""#!/usr/bin/env sh
cd "{project}"
exec "{python}" "{project}/usbshadow.py" open "$@"
"""
    )
    launcher.chmod(launcher.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    ensure_shell_path(bin_dir)

    run(["systemctl", "--user", "daemon-reload"], check=False)
    run(["systemctl", "--user", "enable", "--now", "usbshadow-dashboard.service"], check=False)
    run(["systemctl", "--user", "enable", "--now", "usbshadow-agent.service"], check=False)

    print("\nInstalled Linux user services.")
    print("Command: usb")
    print("Dashboard: http://127.0.0.1:5000")
    print("If 'usb' is not found, add ~/.local/bin to PATH.")


def install_macos() -> None:
    launch_dir = Path.home() / "Library" / "LaunchAgents"
    launch_dir.mkdir(parents=True, exist_ok=True)
    python = str(PYTHON)
    project = str(BASE_DIR)

    dashboard_plist = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
  <key>Label</key><string>com.usbshadow.dashboard</string>
  <key>WorkingDirectory</key><string>{project}</string>
  <key>ProgramArguments</key>
  <array><string>{python}</string><string>{project}/usbshadow.py</string><string>dashboard</string><string>--host</string><string>127.0.0.1</string><string>--port</string><string>5000</string></array>
  <key>RunAtLoad</key><true/>
  <key>KeepAlive</key><true/>
  <key>StandardOutPath</key><string>{project}/logs/dashboard-launchd.log</string>
  <key>StandardErrorPath</key><string>{project}/logs/dashboard-launchd.err</string>
</dict></plist>
"""

    agent_plist = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
  <key>Label</key><string>com.usbshadow.agent</string>
  <key>WorkingDirectory</key><string>{project}</string>
  <key>ProgramArguments</key>
  <array><string>{python}</string><string>{project}/usbshadow.py</string><string>agent</string><string>--platform</string><string>macos</string></array>
  <key>EnvironmentVariables</key><dict><key>USBSHADOW_API</key><string>http://127.0.0.1:5000</string></dict>
  <key>RunAtLoad</key><true/>
  <key>KeepAlive</key><true/>
  <key>StandardOutPath</key><string>{project}/logs/agent-launchd.log</string>
  <key>StandardErrorPath</key><string>{project}/logs/agent-launchd.err</string>
</dict></plist>
"""

    dashboard_path = launch_dir / "com.usbshadow.dashboard.plist"
    agent_path = launch_dir / "com.usbshadow.agent.plist"
    dashboard_path.write_text(dashboard_plist)
    agent_path.write_text(agent_plist)

    bin_dir = Path.home() / ".local" / "bin"
    bin_dir.mkdir(parents=True, exist_ok=True)
    launcher = bin_dir / "usb"
    launcher.write_text(
        f"""#!/usr/bin/env sh
cd "{project}"
exec "{python}" "{project}/usbshadow.py" open "$@"
"""
    )
    launcher.chmod(launcher.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    ensure_shell_path(bin_dir)

    run(["launchctl", "unload", str(dashboard_path)], check=False)
    run(["launchctl", "unload", str(agent_path)], check=False)
    run(["launchctl", "load", str(dashboard_path)], check=False)
    run(["launchctl", "load", str(agent_path)], check=False)

    print("\nInstalled macOS LaunchAgents.")
    print("Command: usb")
    print("Dashboard: http://127.0.0.1:5000")
    print("If 'usb' is not found, add ~/.local/bin to PATH.")


def install_windows() -> None:
    python = str(PYTHON)
    project = str(BASE_DIR)
    usb_cmd = BASE_DIR / "usb.cmd"
    usb_cmd.write_text(
        f"""@echo off
cd /d "{project}"
"{python}" "{project}\\usbshadow.py" open %*
"""
    )

    dashboard_cmd = f'"{python}" "{project}\\usbshadow.py" dashboard --host 127.0.0.1 --port 5000'
    agent_cmd = f'"{python}" "{project}\\usbshadow.py" agent --platform windows'
    run(["schtasks", "/Create", "/TN", "USBSHADOW Dashboard", "/SC", "ONLOGON", "/TR", dashboard_cmd, "/F"], check=False)
    run(["schtasks", "/Create", "/TN", "USBSHADOW Agent", "/SC", "ONLOGON", "/TR", agent_cmd, "/F"], check=False)
    run(["schtasks", "/Run", "/TN", "USBSHADOW Dashboard"], check=False)
    run(["schtasks", "/Run", "/TN", "USBSHADOW Agent"], check=False)

    print("\nInstalled Windows startup tasks.")
    print(f"Command: {usb_cmd}")
    print("Dashboard: http://127.0.0.1:5000")
    print("Add the project folder to PATH if you want to type only: usb")


def main() -> int:
    parser = argparse.ArgumentParser(description="Install USBSHADOW as a background app.")
    parser.add_argument("--no-deps", action="store_true", help="Skip dependency installation")
    args = parser.parse_args()

    if not args.no_deps:
        install_dependencies()
    ensure_env()
    (BASE_DIR / "logs").mkdir(exist_ok=True)

    system = platform.system().lower()
    if system == "linux":
        install_linux()
    elif system == "darwin":
        install_macos()
    elif system == "windows":
        install_windows()
    else:
        raise SystemExit(f"Unsupported OS: {platform.system()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
