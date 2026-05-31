from __future__ import annotations

import json
import logging
import plistlib
import subprocess
import time
from pathlib import Path

from agent.common import register_device, register_event
from agent.file_monitor import monitor_path


LOGGER = logging.getLogger("usbshadow.mac")


def _diskutil_list() -> dict:
    result = subprocess.run(
        ["diskutil", "list", "-plist", "external", "physical"],
        check=False,
        capture_output=True,
    )
    if result.returncode != 0:
        LOGGER.warning("diskutil failed: %s", result.stderr.decode("utf-8", "ignore"))
        return {}
    return plistlib.loads(result.stdout)


def _diskutil_info(identifier: str) -> dict:
    result = subprocess.run(
        ["diskutil", "info", "-plist", identifier],
        check=False,
        capture_output=True,
    )
    if result.returncode != 0:
        return {}
    return plistlib.loads(result.stdout)


def _volumes() -> list[dict]:
    devices = _diskutil_list()
    volumes = []
    for disk in devices.get("AllDisksAndPartitions", []):
        for partition in disk.get("Partitions", []):
            mount = partition.get("MountPoint")
            identifier = partition.get("DeviceIdentifier")
            if not mount or not str(mount).startswith("/Volumes/"):
                continue
            info = _diskutil_info(identifier)
            volumes.append(
                {
                    "identifier": identifier,
                    "mount_point": mount,
                    "info": info,
                }
            )
    return volumes


def _payload(volume: dict) -> dict:
    info = volume.get("info", {})
    return {
        "device_name": info.get("VolumeName") or volume["identifier"],
        "vendor": info.get("DeviceVendor"),
        "manufacturer": info.get("DeviceVendor"),
        "serial_number": info.get("MediaUUID"),
        "vid": info.get("VendorID"),
        "pid": info.get("ProductID"),
        "mount_point": volume["mount_point"],
        "is_active": True,
        "metadata": {"diskutil": json.dumps(info, default=str)[:4000]},
    }


def run(poll_seconds: int = 5) -> None:
    seen: set[str] = set()
    observers = {}
    while True:
        current = {volume["mount_point"]: volume for volume in _volumes()}
        for mount, volume in current.items():
            if mount in seen:
                continue
            payload = _payload(volume)
            LOGGER.info("USB volume detected: %s", payload)
            result = register_device(payload)
            device_id = (result or {}).get("device", {}).get("id")
            if Path(mount).exists():
                observers[mount] = monitor_path(mount, device_id=device_id)
        for removed in seen - set(current):
            observer = observers.pop(removed, None)
            if observer:
                observer.stop()
            register_event({"event_type": "removed", "path": removed})
        seen = set(current)
        time.sleep(poll_seconds)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run()
