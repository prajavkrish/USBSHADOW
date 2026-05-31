from __future__ import annotations

import platform
import subprocess
from pathlib import Path


def run(command: list[str]) -> None:
    print("+", " ".join(command))
    subprocess.run(command, check=False)


def uninstall_linux() -> None:
    run(["systemctl", "--user", "disable", "--now", "usbshadow-agent.service"])
    run(["systemctl", "--user", "disable", "--now", "usbshadow-dashboard.service"])
    service_dir = Path.home() / ".config" / "systemd" / "user"
    for name in ("usbshadow-agent.service", "usbshadow-dashboard.service"):
        path = service_dir / name
        if path.exists():
            path.unlink()
    launcher = Path.home() / ".local" / "bin" / "usb"
    if launcher.exists():
        launcher.unlink()
    run(["systemctl", "--user", "daemon-reload"])


def uninstall_macos() -> None:
    launch_dir = Path.home() / "Library" / "LaunchAgents"
    for name in ("com.usbshadow.agent.plist", "com.usbshadow.dashboard.plist"):
        path = launch_dir / name
        run(["launchctl", "unload", str(path)])
        if path.exists():
            path.unlink()
    launcher = Path.home() / ".local" / "bin" / "usb"
    if launcher.exists():
        launcher.unlink()


def uninstall_windows() -> None:
    run(["schtasks", "/Delete", "/TN", "USBSHADOW Agent", "/F"])
    run(["schtasks", "/Delete", "/TN", "USBSHADOW Dashboard", "/F"])


def main() -> int:
    system = platform.system().lower()
    if system == "linux":
        uninstall_linux()
    elif system == "darwin":
        uninstall_macos()
    elif system == "windows":
        uninstall_windows()
    else:
        raise SystemExit(f"Unsupported OS: {platform.system()}")
    print("USBSHADOW background services removed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
