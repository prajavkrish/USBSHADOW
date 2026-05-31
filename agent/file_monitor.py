from __future__ import annotations

import logging
import time
from pathlib import Path

from watchdog.events import FileSystemEvent, FileSystemEventHandler
from watchdog.observers import Observer

from agent.common import register_event, sha256_file


LOGGER = logging.getLogger("usbshadow.file_monitor")


class USBFileActivityHandler(FileSystemEventHandler):
    def __init__(self, device_id: int | None = None) -> None:
        super().__init__()
        self.device_id = device_id

    def _emit(self, event_type: str, path: str, metadata: dict | None = None) -> None:
        file_path = Path(path)
        if file_path.is_dir():
            return
        sha256 = sha256_file(file_path) if event_type != "deleted" else None
        size = file_path.stat().st_size if file_path.exists() else None
        register_event(
            {
                "device_id": self.device_id,
                "event_type": event_type,
                "path": str(file_path),
                "filename": file_path.name,
                "file_size": size,
                "sha256": sha256,
                "metadata": metadata or {},
            }
        )

    def on_created(self, event: FileSystemEvent) -> None:
        self._emit("created", event.src_path)

    def on_modified(self, event: FileSystemEvent) -> None:
        self._emit("modified", event.src_path)

    def on_deleted(self, event: FileSystemEvent) -> None:
        self._emit("deleted", event.src_path)

    def on_moved(self, event: FileSystemEvent) -> None:
        self._emit("moved", event.dest_path, {"source_path": event.src_path})


def monitor_path(path: str, device_id: int | None = None) -> Observer:
    observer = Observer()
    observer.schedule(USBFileActivityHandler(device_id=device_id), path, recursive=True)
    observer.start()
    LOGGER.info("Watching USB path %s", path)
    return observer


def run_forever(path: str, device_id: int | None = None) -> None:
    observer = monitor_path(path, device_id=device_id)
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Monitor USB file activity")
    parser.add_argument("path")
    parser.add_argument("--device-id", type=int)
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO)
    run_forever(args.path, args.device_id)

