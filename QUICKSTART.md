# USBSHADOW Quickstart

USBSHADOW is meant to be installed once and then run in the background.

- The background dashboard listens on `127.0.0.1:5000`.
- The background agent watches USB insert/remove activity.
- The user types `usb` when they want to see the dashboard.

## Install

Linux/macOS:

```bash
python3 install.py
```

Windows PowerShell:

```powershell
py install.py
```

After install, USBSHADOW starts automatically whenever the user logs in.

## Open The Dashboard

Type:

```bash
usb
```

That opens:

```text
http://127.0.0.1:5000
```

If `usb` is not found on Linux/macOS, add this to the shell profile:

```bash
export PATH="$HOME/.local/bin:$PATH"
```

## What Happens In The Background

When the system starts or the user logs in:

1. `usbshadow-dashboard` starts the local web dashboard.
2. `usbshadow-agent` starts the USB monitor.
3. USB insertions/removals are recorded automatically.
4. Mounted USB folders are watched for file create/modify/delete/move events.
5. Evidence and incidents appear in the dashboard.

## Manual Commands

You can still run commands manually:

```bash
python usbshadow.py open
python usbshadow.py dashboard
python usbshadow.py agent
```

## Watch A Specific USB Folder

Only use this when you know the mounted USB path and want to force file monitoring.

Linux example:

```bash
python usbshadow.py file-watch /media/$USER/USB
```

macOS example:

```bash
python usbshadow.py file-watch /Volumes/USB
```

Do not type `/path/to/mounted/usb` literally. It is only a placeholder.

## Uninstall

```bash
python3 uninstall.py
```
