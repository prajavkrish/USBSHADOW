from __future__ import annotations

import logging
import subprocess
import time
from pathlib import Path

import pyudev

from agent.common import host_context, register_device, register_event
from agent.file_monitor import monitor_path


LOGGER = logging.getLogger("usbshadow.linux")


def _mount_point(device_node: str | None) -> str | None:
    if not device_node:
        return None
    try:
        result = subprocess.run(
            ["findmnt", "-n", "-o", "TARGET", "--source", device_node],
            check=False,
            capture_output=True,
            text=True,
        )
    except OSError:
        return None
    mount = result.stdout.strip().splitlines()
    return mount[0] if mount else None


def _device_payload(device: pyudev.Device) -> dict:
    parent = device.find_parent("usb", "usb_device")
    mount = _mount_point(device.device_node)
    return {
        "device_name": device.get("ID_MODEL") or device.sys_name,
        "vendor": device.get("ID_VENDOR"),
        "manufacturer": parent.get("manufacturer") if parent else device.get("ID_VENDOR"),
        "serial_number": device.get("ID_SERIAL_SHORT"),
        "vid": parent.get("idVendor") if parent else device.get("ID_VENDOR_ID"),
        "pid": parent.get("idProduct") if parent else device.get("ID_MODEL_ID"),
        "mount_point": mount,
        "is_active": True,
    }


def run() -> None:
    context = pyudev.Context()
    monitor = pyudev.Monitor.from_netlink(context)
    monitor.filter_by(subsystem="block")
    observers = []
    for action, device in monitor:
        if device.get("ID_BUS") != "usb":
            continue
        payload = _device_payload(device)
        if action in {"add", "change"}:
            LOGGER.info("USB device detected: %s", payload)
            result = register_device(payload)
            device_id = (result or {}).get("device", {}).get("id")
            mount = payload.get("mount_point")
            if mount and Path(mount).exists():
                observers.append(monitor_path(mount, device_id=device_id))
        elif action == "remove":
            register_event(
                {
                    **host_context(),
                    "event_type": "removed",
                    "metadata": {"device_node": device.device_node},
                }
            )
        time.sleep(0.5)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run()

