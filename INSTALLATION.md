# USBSHADOW Installation Guide

USBSHADOW installs as a background app.

After installation:

- The dashboard starts automatically at login.
- The USB monitor starts automatically at login.
- The user types `usb` to open the dashboard.
- USB activity is collected in the background.

## Linux

```bash
cd USBSHADOW
python3 install.py
```

The installer creates:

- `~/.config/systemd/user/usbshadow-dashboard.service`
- `~/.config/systemd/user/usbshadow-agent.service`
- `~/.local/bin/usb`

Useful service commands:

```bash
systemctl --user status usbshadow-dashboard.service
systemctl --user status usbshadow-agent.service
systemctl --user restart usbshadow-dashboard.service
systemctl --user restart usbshadow-agent.service
```

Open dashboard:

```bash
usb
```

If `usb` is not found:

```bash
export PATH="$HOME/.local/bin:$PATH"
```

## macOS

```bash
cd USBSHADOW
python3 install.py
```

The installer creates:

- `~/Library/LaunchAgents/com.usbshadow.dashboard.plist`
- `~/Library/LaunchAgents/com.usbshadow.agent.plist`
- `~/.local/bin/usb`

Open dashboard:

```bash
usb
```

The dashboard runs at:

```text
http://127.0.0.1:5000
```

## Windows

Open PowerShell in the project folder:

```powershell
py install.py
```

The installer creates Scheduled Tasks:

- `USBSHADOW Dashboard`
- `USBSHADOW Agent`

Open dashboard:

```powershell
.\usb.cmd
```

To type only `usb`, add the project folder to the user PATH.

## How USB Detection Works

Linux:

- `usbshadow-agent.service` runs `pyudev`.
- It listens for USB block devices.
- When a USB is inserted, it records metadata and mount point.
- If the mount point is available, file monitoring starts.

Windows:

- The scheduled agent uses WMI.
- It polls USB disk drives.
- It records drive letter, device name, PNP ID, serial number, VID, and PID.

macOS:

- The LaunchAgent calls `diskutil`.
- It detects external physical disks and mounted volumes under `/Volumes`.
- It starts file monitoring for mounted USB volumes.

## What The User Sees

The user does not need terminals open.

They type:

```bash
usb
```

Then the browser opens the SOC dashboard with:

- Device inventory
- USB timeline
- File activity
- SHA256 evidence
- Risk incidents
- Analytics

## Uninstall

```bash
python3 uninstall.py
```
