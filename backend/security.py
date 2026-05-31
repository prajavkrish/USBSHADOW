from __future__ import annotations

from flask import abort


SAFE_EVENT_TYPES = {
    "inserted",
    "removed",
    "created",
    "modified",
    "deleted",
    "moved",
}


def clean_string(value: object, max_length: int, required: bool = False) -> str | None:
    if value is None:
        if required:
            abort(400, "Missing required field")
        return None
    if not isinstance(value, str):
        value = str(value)
    value = value.strip()
    if required and not value:
        abort(400, "Missing required field")
    if len(value) > max_length:
        abort(400, f"Field exceeds {max_length} characters")
    return value or None


def validate_device_payload(payload: dict) -> dict:
    if not isinstance(payload, dict):
        abort(400, "JSON body is required")
    return {
        "device_name": clean_string(payload.get("device_name"), 255, required=True),
        "vendor": clean_string(payload.get("vendor"), 255),
        "manufacturer": clean_string(payload.get("manufacturer"), 255),
        "serial_number": clean_string(payload.get("serial_number"), 255),
        "vid": clean_string(payload.get("vid"), 32),
        "pid": clean_string(payload.get("pid"), 32),
        "username": clean_string(payload.get("username"), 255),
        "hostname": clean_string(payload.get("hostname"), 255),
        "platform": clean_string(payload.get("platform"), 64),
        "mount_point": clean_string(payload.get("mount_point"), 1024),
        "is_active": bool(payload.get("is_active", True)),
    }


def validate_event_payload(payload: dict) -> dict:
    if not isinstance(payload, dict):
        abort(400, "JSON body is required")
    event_type = clean_string(payload.get("event_type"), 64, required=True)
    if event_type not in SAFE_EVENT_TYPES:
        abort(400, "Unsupported event type")
    file_size = payload.get("file_size")
    if file_size is not None:
        try:
            file_size = int(file_size)
        except (TypeError, ValueError):
            abort(400, "file_size must be an integer")
        if file_size < 0:
            abort(400, "file_size cannot be negative")
    return {
        "device_id": payload.get("device_id"),
        "event_type": event_type,
        "username": clean_string(payload.get("username"), 255),
        "hostname": clean_string(payload.get("hostname"), 255),
        "path": clean_string(payload.get("path"), 2048),
        "filename": clean_string(payload.get("filename"), 512),
        "file_size": file_size,
        "sha256": clean_string(payload.get("sha256"), 64),
        "event_metadata": payload.get("metadata") if isinstance(payload.get("metadata"), dict) else {},
    }
