import os
from pathlib import Path

from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


def database_url() -> str:
    configured = os.getenv("DATABASE_URL")
    if not configured:
        return f"sqlite:///{BASE_DIR / 'usbshadow.db'}"
    if configured.startswith("sqlite:///") and not configured.startswith("sqlite:////"):
        sqlite_path = configured.removeprefix("sqlite:///")
        return f"sqlite:///{BASE_DIR / sqlite_path}"
    return configured


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "change-me-in-production")
    SQLALCHEMY_DATABASE_URI = database_url()
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JSON_SORT_KEYS = False
    MAX_CONTENT_LENGTH = int(os.getenv("MAX_CONTENT_LENGTH", 16 * 1024 * 1024))
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    APP_TIMEZONE = os.getenv("APP_TIMEZONE", "Asia/Kolkata")
    SENSITIVE_EXTENSIONS = {
        item.strip().lower()
        for item in os.getenv(
            "SENSITIVE_EXTENSIONS",
            ".key,.pem,.pfx,.p12,.kdbx,.docx,.xlsx,.pdf,.sql,.env",
        ).split(",")
        if item.strip()
    }
    LARGE_FILE_BYTES = int(os.getenv("LARGE_FILE_BYTES", 100 * 1024 * 1024))
    REPEATED_CONNECTION_WINDOW_HOURS = int(
        os.getenv("REPEATED_CONNECTION_WINDOW_HOURS", 24)
    )
    REPEATED_CONNECTION_THRESHOLD = int(
        os.getenv("REPEATED_CONNECTION_THRESHOLD", 3)
    )
