from __future__ import annotations

from datetime import datetime, timezone

from flask_sqlalchemy import SQLAlchemy


db = SQLAlchemy()


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class USBDevice(db.Model):
    __tablename__ = "usb_devices"

    id = db.Column(db.Integer, primary_key=True)
    device_name = db.Column(db.String(255), nullable=False, index=True)
    vendor = db.Column(db.String(255), nullable=True, index=True)
    manufacturer = db.Column(db.String(255), nullable=True)
    serial_number = db.Column(db.String(255), nullable=True, index=True)
    vid = db.Column(db.String(32), nullable=True, index=True)
    pid = db.Column(db.String(32), nullable=True, index=True)
    username = db.Column(db.String(255), nullable=True)
    hostname = db.Column(db.String(255), nullable=True, index=True)
    platform = db.Column(db.String(64), nullable=True)
    mount_point = db.Column(db.String(1024), nullable=True)
    is_active = db.Column(db.Boolean, default=False, nullable=False, index=True)
    first_seen = db.Column(db.DateTime(timezone=True), default=utcnow, nullable=False)
    last_seen = db.Column(db.DateTime(timezone=True), default=utcnow, nullable=False)

    events = db.relationship(
        "USBEvent", back_populates="device", cascade="all, delete-orphan"
    )
    evidences = db.relationship(
        "Evidence", back_populates="device", cascade="all, delete-orphan"
    )
    incidents = db.relationship(
        "Incident", back_populates="device", cascade="all, delete-orphan"
    )

    def fingerprint(self) -> tuple[str | None, str | None, str | None]:
        return self.serial_number, self.vid, self.pid

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "device_name": self.device_name,
            "vendor": self.vendor,
            "manufacturer": self.manufacturer,
            "serial_number": self.serial_number,
            "vid": self.vid,
            "pid": self.pid,
            "username": self.username,
            "hostname": self.hostname,
            "platform": self.platform,
            "mount_point": self.mount_point,
            "is_active": self.is_active,
            "first_seen": self.first_seen.isoformat(),
            "last_seen": self.last_seen.isoformat(),
        }


class USBEvent(db.Model):
    __tablename__ = "usb_events"

    id = db.Column(db.Integer, primary_key=True)
    device_id = db.Column(
        db.Integer, db.ForeignKey("usb_devices.id"), nullable=True, index=True
    )
    event_type = db.Column(db.String(64), nullable=False, index=True)
    timestamp = db.Column(db.DateTime(timezone=True), default=utcnow, nullable=False)
    username = db.Column(db.String(255), nullable=True)
    hostname = db.Column(db.String(255), nullable=True, index=True)
    path = db.Column(db.String(2048), nullable=True)
    filename = db.Column(db.String(512), nullable=True)
    file_size = db.Column(db.Integer, nullable=True)
    sha256 = db.Column(db.String(64), nullable=True, index=True)
    event_metadata = db.Column("metadata", db.JSON, nullable=True)

    device = db.relationship("USBDevice", back_populates="events")
    evidences = db.relationship(
        "Evidence", back_populates="event", cascade="all, delete-orphan"
    )
    incidents = db.relationship(
        "Incident", back_populates="event", cascade="all, delete-orphan"
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "device_id": self.device_id,
            "event_type": self.event_type,
            "timestamp": self.timestamp.isoformat(),
            "username": self.username,
            "hostname": self.hostname,
            "path": self.path,
            "filename": self.filename,
            "file_size": self.file_size,
            "sha256": self.sha256,
            "metadata": self.event_metadata or {},
        }


class Evidence(db.Model):
    __tablename__ = "evidence"

    id = db.Column(db.Integer, primary_key=True)
    device_id = db.Column(
        db.Integer, db.ForeignKey("usb_devices.id"), nullable=True, index=True
    )
    event_id = db.Column(
        db.Integer, db.ForeignKey("usb_events.id"), nullable=True, index=True
    )
    evidence_type = db.Column(db.String(64), nullable=False, index=True)
    filename = db.Column(db.String(512), nullable=True)
    path = db.Column(db.String(2048), nullable=True)
    sha256 = db.Column(db.String(64), nullable=True, index=True)
    collected_at = db.Column(db.DateTime(timezone=True), default=utcnow, nullable=False)
    details = db.Column(db.JSON, nullable=True)

    device = db.relationship("USBDevice", back_populates="evidences")
    event = db.relationship("USBEvent", back_populates="evidences")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "device_id": self.device_id,
            "event_id": self.event_id,
            "evidence_type": self.evidence_type,
            "filename": self.filename,
            "path": self.path,
            "sha256": self.sha256,
            "collected_at": self.collected_at.isoformat(),
            "details": self.details or {},
        }


class Incident(db.Model):
    __tablename__ = "incidents"

    id = db.Column(db.Integer, primary_key=True)
    device_id = db.Column(
        db.Integer, db.ForeignKey("usb_devices.id"), nullable=True, index=True
    )
    event_id = db.Column(
        db.Integer, db.ForeignKey("usb_events.id"), nullable=True, index=True
    )
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)
    threat_score = db.Column(db.Integer, nullable=False, default=0, index=True)
    risk_level = db.Column(db.String(32), nullable=False, default="Low", index=True)
    status = db.Column(db.String(32), nullable=False, default="Open", index=True)
    created_at = db.Column(db.DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at = db.Column(
        db.DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False
    )
    factors = db.Column(db.JSON, nullable=True)

    device = db.relationship("USBDevice", back_populates="incidents")
    event = db.relationship("USBEvent", back_populates="incidents")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "device_id": self.device_id,
            "event_id": self.event_id,
            "title": self.title,
            "description": self.description,
            "threat_score": self.threat_score,
            "risk_level": self.risk_level,
            "status": self.status,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "factors": self.factors or [],
        }
