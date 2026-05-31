```ruby
 __ __  _____ ____          _____ __ __   ____  ___     ___   __    __ 
|  |  |/ ___/|    \        / ___/|  |  | /    ||   \   /   \ |  |__|  |
|  |  (   \_ |  o  ) _____(   \_ |  |  ||  o  ||    \ |     ||  |  |  |
|  |  |\__  ||     ||     |\__  ||  _  ||     ||  D  ||  O  ||  |  |  |
|  :  |/  \ ||  O  ||_____|/  \ ||  |  ||  _  ||     ||     ||  `  '  |
|     |\    ||     |       \    ||  |  ||  |  ||     ||     | \      / 
 \__,_| \___||_____|        \___||__|__||__|__||_____| \___/   \_/\_/  
```                                                                       

Cross-platform USB forensics, monitoring, and incident scoring for Windows, Linux, and macOS.

USBSHADOW installs once, runs in the background, detects USB activity, watches mounted USB file changes, stores forensic evidence, and exposes a cyber SOC-style dashboard.

```bash
python3 install.py
usb
```

## Demo And Preview

- Demo website: [https://prajavkrish.github.io/USBSHADOW/](https://prajavkrish.github.io/USBSHADOW/)
- Local dashboard: `http://127.0.0.1:5000`
- Static demo source: [docs/index.html](docs/index.html)

> The demo website is a static preview for GitHub Pages. Real USB monitoring runs locally because the agent needs host OS access to USB events.

![KRZX-MYTHOZ Dashboard Preview](screenshots/dashboard-preview.svg)

## Core Features

- Background USB monitoring agent.
- Browser dashboard/API on `127.0.0.1:5000`.
- One-word dashboard launcher: `usb`.
- Windows USB detection through WMI.
- Linux USB detection through `pyudev`.
- macOS USB volume detection through `diskutil`.
- Device fingerprinting with name, vendor, manufacturer, serial number, VID, PID, username, hostname, platform, and mount point.
- USB file activity monitoring through `watchdog`.
- SHA256 evidence collection.
- Threat scoring and incident generation.
- SQLite by default, PostgreSQL support through `DATABASE_URL`.
- Waitress + Flask backend.
- Bootstrap 5 + Chart.js cyber dashboard.

## User Installation

### Linux/macOS

```bash
cd USBSHADOW
python3 install.py
```

Open the dashboard:

```bash
usb
```

If `usb` is not found in the current terminal:

```bash
source ~/.profile
```

Or add this to your shell profile:

```bash
export PATH="$HOME/.local/bin:$PATH"
```

### Windows

Open PowerShell in the project folder:

```powershell
py install.py
```

Open the dashboard:

```powershell
.\usb.cmd
```

To type only `usb`, add the project folder to the user PATH.

## Background Runtime

After install, USBSHADOW starts automatically when the user logs in.

Linux creates:

- `~/.config/systemd/user/usbshadow-dashboard.service`
- `~/.config/systemd/user/usbshadow-agent.service`
- `~/.local/bin/usb`

Linux service commands:

```bash
systemctl --user status usbshadow-dashboard.service
systemctl --user status usbshadow-agent.service
systemctl --user restart usbshadow-dashboard.service
systemctl --user restart usbshadow-agent.service
```

macOS creates:

- `~/Library/LaunchAgents/com.usbshadow.dashboard.plist`
- `~/Library/LaunchAgents/com.usbshadow.agent.plist`
- `~/.local/bin/usb`

Windows creates:

- Scheduled Task: `USBSHADOW Dashboard`
- Scheduled Task: `USBSHADOW Agent`
- Launcher: `usb.cmd`

## How USB Detection Works

Linux:

- `pyudev` listens for block-device events.
- USB storage insertions/removals are detected.
- `findmnt` resolves mount points.
- Device metadata is posted to `/api/device`.
- Mounted USB paths are watched with `watchdog`.

Windows:

- WMI checks `Win32_DiskDrive` where `InterfaceType="USB"`.
- USB disks are mapped to partitions and drive letters.
- PNP metadata is parsed for serial number, VID, PID, name, and manufacturer.
- Mounted drive letters are watched with `watchdog`.

macOS:

- `diskutil list -plist external physical` detects external disks.
- `diskutil info -plist` collects volume metadata.
- Volumes mounted under `/Volumes` are watched with `watchdog`.

## File Activity Monitoring

USBSHADOW captures:

- File creation
- File modification
- File deletion
- File movement

Evidence fields:

- Filename
- Full path
- Timestamp
- File size
- SHA256 hash when readable
- Device relationship
- Username and hostname

Manual watch examples:

```bash
python usbshadow.py file-watch /media/$USER/USB
python usbshadow.py file-watch /Volumes/USB
```

## Threat Scoring

| Indicator | Score |
| --- | ---: |
| Unknown USB | +40 |
| Large file transfer | +30 |
| Multiple sensitive files | +25 |
| Repeated connections | +15 |

Risk levels:

| Score | Level |
| --- | --- |
| 0-30 | Low |
| 31-60 | Medium |
| 61-100 | High |

Scores are capped at 100. Any non-zero score creates an incident.

## Dashboard Pages

- Overview: SOC summary, priority queue, active devices, USB timeline, and threat distribution.
- Devices: searchable/filterable USB inventory.
- Events: USB insertion/removal and file activity timeline.
- Incidents: scored risk events with report links.
- Analytics: threat, platform, and event charts.
- Incident Reports: device metadata, event details, scoring factors, and evidence links.

## Architecture

```mermaid
flowchart LR
    OS[User Login / System Startup] --> SVC[Background Service]
    SVC --> DASH[Dashboard API<br>Waitress + Flask]
    SVC --> AGENT[USB Agent]
    W[Windows<br>WMI] --> AGENT
    L[Linux<br>pyudev] --> AGENT
    M[macOS<br>diskutil] --> AGENT
    AGENT --> API[REST API]
    FILES[watchdog File Monitor] --> API
    API --> SCORE[Threat Scoring Engine]
    API --> DB[(SQLite / PostgreSQL)]
    API --> EV[Evidence Records]
    DB --> UI[SOC Dashboard]
    USER[User types usb] --> UI
```

## Project Structure

```text
USBSHADOW/
├── agent/
│   ├── windows_monitor.py
│   ├── linux_monitor.py
│   ├── mac_monitor.py
│   └── file_monitor.py
├── backend/
│   ├── app.py
│   ├── models.py
│   ├── routes.py
│   ├── scoring.py
│   ├── security.py
│   ├── time_utils.py
│   └── config.py
├── dashboard/
│   ├── templates/
│   └── static/
├── docs/
│   ├── index.html
│   └── dashboard-preview.svg
├── evidence/
├── logs/
├── screenshots/
│   └── dashboard-preview.svg
├── install.py
├── uninstall.py
├── usb
├── usb.cmd
├── usbshadow.py
├── requirements.txt
├── docker-compose.yml
├── Dockerfile
└── .env.example
```

## Database

Default SQLite:

```env
DATABASE_URL=sqlite:///usbshadow.db
```

PostgreSQL:

```env
DATABASE_URL=postgresql+psycopg://usbshadow:usbshadow@localhost:5432/usbshadow
```

Models:

- `USBDevice`
- `USBEvent`
- `Evidence`
- `Incident`

## REST API

All API responses are JSON.

| Method | Endpoint | Description |
| --- | --- | --- |
| `GET` | `/api/devices` | Paginated USB device inventory |
| `GET` | `/api/events` | Paginated USB and file activity events |
| `GET` | `/api/incidents` | Paginated scored incidents |
| `GET` | `/api/evidence` | Paginated evidence records |
| `GET` | `/api/analytics/summary` | Threat/platform/event chart data |
| `POST` | `/api/device` | Register or update USB device |
| `POST` | `/api/event` | Create USB or file activity event |

Create device:

```json
{
  "device_name": "SanDisk Ultra",
  "vendor": "SanDisk",
  "manufacturer": "SanDisk",
  "serial_number": "123456789",
  "vid": "0781",
  "pid": "5581",
  "username": "analyst",
  "hostname": "workstation-01",
  "platform": "linux",
  "mount_point": "/media/analyst/USB",
  "is_active": true
}
```

Create event:

```json
{
  "device_id": 1,
  "event_type": "created",
  "path": "/media/analyst/USB/report.pdf",
  "filename": "report.pdf",
  "file_size": 204800,
  "sha256": "64-character-sha256",
  "metadata": {
    "source": "watchdog"
  }
}
```

Supported event types:

- `inserted`
- `removed`
- `created`
- `modified`
- `deleted`
- `moved`

## Configuration

Copy `.env.example` to `.env` and adjust as needed.

Important values:

- `SECRET_KEY`
- `DATABASE_URL`
- `APP_TIMEZONE`
- `USBSHADOW_API`
- `LARGE_FILE_BYTES`
- `SENSITIVE_EXTENSIONS`
- `REPEATED_CONNECTION_WINDOW_HOURS`
- `REPEATED_CONNECTION_THRESHOLD`

## Docker Deployment

Docker is best for the dashboard/API/database. USB hardware monitoring should usually run on the host OS because containers do not automatically receive host USB events.

```bash
docker compose up --build
```

Open:

```text
http://127.0.0.1:5000
```

## Development Commands

```bash
python usbshadow.py dashboard
python usbshadow.py agent
python usbshadow.py open
python usbshadow.py status
python usbshadow.py file-watch /media/$USER/USB
```

## Uninstall

```bash
python3 uninstall.py
```

This removes services/tasks and launchers. It does not delete the database, logs, or evidence files.

## Troubleshooting

Dashboard does not open:

```bash
python usbshadow.py open
```

Port `5000` is already in use:

```bash
python usbshadow.py dashboard --port 5001
```

`usb` is not found on Linux/macOS:

```bash
source ~/.profile
```

USB devices are not detected on Linux:

- Check `systemctl --user status usbshadow-agent.service`.
- Confirm the device appears in `lsblk`.
- Confirm the USB has a mount path.

File activity is not detected:

- Confirm the USB volume is mounted.
- Confirm the agent user can read the USB path.
- Run `python usbshadow.py file-watch /media/$USER/USB`.

## GitHub Pages Demo Setup

After pushing to GitHub:

1. Open repository settings.
2. Go to `Pages`.
3. Select branch `main`.
4. Select folder `/docs`.
5. Save.

The demo will be available at:

```text
https://prajavkrish.github.io/USBSHADOW/
```

## Before Pushing To GitHub

```bash
python -m compileall agent backend usbshadow.py install.py uninstall.py
git status
git add .
git commit -m "Build KRZX-MYTHOZ USB forensics platform"
git push origin main
```

Do not commit:

- `.env`
- `.venv/`
- `usbshadow.db`
- logs
- collected evidence

## Security Notes

- Change `SECRET_KEY` before real deployment.
- Keep the dashboard bound to `127.0.0.1` unless remote access is intentional.
- Add authentication/RBAC before exposing the dashboard on a network.
- Treat evidence paths, hashes, usernames, hostnames, and incident records as sensitive data.
- Use PostgreSQL for multi-host or long-term deployments.

## License

This project is licensed under the [MIT License](LICENSE).
