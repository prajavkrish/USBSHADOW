from __future__ import annotations

import logging
import time

import wmi

from agent.common import register_device, register_event
from agent.file_monitor import monitor_path


LOGGER = logging.getLogger("usbshadow.windows")


def _payload(logical_disk, disk_drive) -> dict:
    pnp_id = getattr(disk_drive, "PNPDeviceID", "") or ""
    parts = pnp_id.split("\\")
    serial = parts[-1].split("&")[0] if parts else None
    vid = None
    pid = None
    for item in pnp_id.split("&"):
        if item.startswith("VID_"):
            vid = item.replace("VID_", "")
        if item.startswith("PID_"):
            pid = item.replace("PID_", "")
    return {
        "device_name": getattr(disk_drive, "Caption", None) or logical_disk.DeviceID,
        "vendor": getattr(disk_drive, "Manufacturer", None),
        "manufacturer": getattr(disk_drive, "Manufacturer", None),
        "serial_number": serial,
        "vid": vid,
        "pid": pid,
        "mount_point": f"{logical_disk.DeviceID}\\",
        "is_active": True,
    }


def _usb_disks(client):
    for disk in client.Win32_DiskDrive(InterfaceType="USB"):
        for partition in disk.associators("Win32_DiskDriveToDiskPartition"):
            for logical in partition.associators("Win32_LogicalDiskToPartition"):
                yield logical, disk


def run(poll_seconds: int = 5) -> None:
    client = wmi.WMI()
    seen: set[str] = set()
    observers = {}
    while True:
        current: set[str] = set()
        for logical, disk in _usb_disks(client):
            mount = f"{logical.DeviceID}\\"
            current.add(mount)
            if mount in seen:
                continue
            payload = _payload(logical, disk)
            LOGGER.info("USB device detected: %s", payload)
            result = register_device(payload)
            device_id = (result or {}).get("device", {}).get("id")
            observers[mount] = monitor_path(mount, device_id=device_id)
        for removed in seen - current:
            observer = observers.pop(removed, None)
            if observer:
                observer.stop()
            register_event({"event_type": "removed", "path": removed})
        seen = current
        time.sleep(poll_seconds)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run()

