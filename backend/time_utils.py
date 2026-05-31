from __future__ import annotations

from datetime import datetime, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


def localize_datetime(value: datetime | None, timezone_name: str) -> datetime | None:
    if value is None:
        return None
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    try:
        target_tz = ZoneInfo(timezone_name)
    except ZoneInfoNotFoundError:
        target_tz = datetime.now().astimezone().tzinfo
    return value.astimezone(target_tz)


def format_local_datetime(
    value: datetime | None,
    timezone_name: str,
    fmt: str = "%Y-%m-%d %H:%M:%S",
) -> str:
    localized = localize_datetime(value, timezone_name)
    return localized.strftime(fmt) if localized else "-"
