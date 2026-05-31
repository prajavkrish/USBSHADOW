from __future__ import annotations

from datetime import timedelta
from pathlib import Path

from flask import current_app

from backend.models import USBDevice, USBEvent, utcnow


def risk_level(score: int) -> str:
    if score <= 30:
        return "Low"
    if score <= 60:
        return "Medium"
    return "High"


def score_event(device: USBDevice | None, event: USBEvent, known_device: bool) -> tuple[int, list[dict]]:
    score = 0
    factors: list[dict] = []
    config = current_app.config

    if event.event_type == "inserted" and not known_device:
        score += 40
        factors.append({"name": "Unknown USB", "score": 40})

    if event.file_size and event.file_size >= config["LARGE_FILE_BYTES"]:
        score += 30
        factors.append({"name": "Large File Transfer", "score": 30})

    sensitive_count = 0
    extensions = config["SENSITIVE_EXTENSIONS"]
    filename = event.filename or ""
    if Path(filename).suffix.lower() in extensions:
        sensitive_count = int((event.event_metadata or {}).get("sensitive_count", 1))
    if sensitive_count >= 2:
        score += 25
        factors.append({"name": "Multiple Sensitive Files", "score": 25})
    elif sensitive_count == 1:
        score += 10
        factors.append({"name": "Sensitive File Activity", "score": 10})

    if device and event.event_type == "inserted":
        window_start = utcnow() - timedelta(
            hours=config["REPEATED_CONNECTION_WINDOW_HOURS"]
        )
        repeated = USBEvent.query.filter(
            USBEvent.device_id == device.id,
            USBEvent.event_type == "inserted",
            USBEvent.timestamp >= window_start,
        ).count()
        if repeated >= config["REPEATED_CONNECTION_THRESHOLD"]:
            score += 15
            factors.append({"name": "Repeated Connections", "score": 15})

    score = min(score, 100)
    return score, factors
