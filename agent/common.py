from __future__ import annotations

import getpass
import hashlib
import logging
import os
import platform
import socket
from pathlib import Path
from typing import Any

import requests


LOGGER = logging.getLogger("usbshadow.agent")
API_BASE = os.getenv("USBSHADOW_API", "http://127.0.0.1:5000")


def host_context() -> dict[str, str]:
    return {
        "username": getpass.getuser(),
        "hostname": socket.gethostname(),
        "platform": platform.system().lower(),
    }


def sha256_file(path: str | Path, chunk_size: int = 1024 * 1024) -> str | None:
    file_path = Path(path)
    if not file_path.is_file():
        return None
    digest = hashlib.sha256()
    try:
        with file_path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(chunk_size), b""):
                digest.update(chunk)
    except (OSError, PermissionError):
        LOGGER.exception("Unable to hash file: %s", file_path)
        return None
    return digest.hexdigest()


def post_json(endpoint: str, payload: dict[str, Any]) -> dict[str, Any] | None:
    url = f"{API_BASE.rstrip('/')}{endpoint}"
    try:
        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.RequestException:
        LOGGER.exception("Failed to post event to %s", url)
        return None


def register_device(payload: dict[str, Any]) -> dict[str, Any] | None:
    enriched = {**host_context(), **payload}
    return post_json("/api/device", enriched)


def register_event(payload: dict[str, Any]) -> dict[str, Any] | None:
    enriched = {**host_context(), **payload}
    return post_json("/api/event", enriched)

