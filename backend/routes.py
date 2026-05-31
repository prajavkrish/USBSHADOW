from __future__ import annotations

from datetime import datetime, timezone

from flask import Blueprint, jsonify, render_template, request
from sqlalchemy import func, or_

from backend.models import Evidence, Incident, USBDevice, USBEvent, db
from backend.scoring import risk_level, score_event
from backend.security import validate_device_payload, validate_event_payload


bp = Blueprint(
    "usbshadow",
    __name__,
    template_folder="../dashboard/templates",
    static_folder="../dashboard/static",
)


def _pagination(model):
    page = max(int(request.args.get("page", 1)), 1)
    per_page = min(max(int(request.args.get("per_page", 50)), 1), 200)
    return model.query.order_by(model.id.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )


def _find_existing_device(data: dict) -> USBDevice | None:
    query = USBDevice.query
    if data.get("serial_number") and data.get("vid") and data.get("pid"):
        return query.filter_by(
            serial_number=data["serial_number"], vid=data["vid"], pid=data["pid"]
        ).first()
    if data.get("serial_number"):
        return query.filter_by(serial_number=data["serial_number"]).first()
    return None


def _upsert_device(data: dict) -> tuple[USBDevice, bool]:
    device = _find_existing_device(data)
    is_new = device is None
    now = datetime.now(timezone.utc)
    if is_new:
        device = USBDevice(first_seen=now)
        db.session.add(device)
    for key, value in data.items():
        setattr(device, key, value)
    device.last_seen = now
    return device, is_new


def _create_incident_if_needed(device: USBDevice | None, event: USBEvent, known_device: bool):
    score, factors = score_event(device, event, known_device)
    if score == 0:
        return None
    incident = Incident(
        device=device,
        event=event,
        title=f"{risk_level(score)} risk USB activity",
        description=f"{event.event_type} event generated a score of {score}.",
        threat_score=score,
        risk_level=risk_level(score),
        factors=factors,
    )
    db.session.add(incident)
    return incident


@bp.get("/")
def overview():
    total_devices = USBDevice.query.count()
    active_devices = USBDevice.query.filter_by(is_active=True).count()
    incidents = Incident.query.count()
    high_risk = Incident.query.filter_by(risk_level="High").count()
    evidence_count = Evidence.query.count()
    event_count = USBEvent.query.count()
    threat_rows = (
        db.session.query(Incident.risk_level, func.count(Incident.id))
        .group_by(Incident.risk_level)
        .all()
    )
    recent_events = USBEvent.query.order_by(USBEvent.timestamp.desc()).limit(10).all()
    recent_incidents = Incident.query.order_by(
        Incident.threat_score.desc(), Incident.created_at.desc()
    ).limit(5).all()
    active_device_rows = USBDevice.query.filter_by(is_active=True).order_by(
        USBDevice.last_seen.desc()
    ).limit(6).all()
    return render_template(
        "overview.html",
        total_devices=total_devices,
        active_devices=active_devices,
        incidents=incidents,
        high_risk=high_risk,
        evidence_count=evidence_count,
        event_count=event_count,
        threat_summary={row[0]: row[1] for row in threat_rows},
        recent_events=recent_events,
        recent_incidents=recent_incidents,
        active_device_rows=active_device_rows,
    )


@bp.get("/devices")
def devices_page():
    query_text = request.args.get("q", "").strip()
    status = request.args.get("status", "").strip()
    query = USBDevice.query
    if query_text:
        pattern = f"%{query_text}%"
        query = query.filter(
            or_(
                USBDevice.device_name.ilike(pattern),
                USBDevice.vendor.ilike(pattern),
                USBDevice.serial_number.ilike(pattern),
                USBDevice.hostname.ilike(pattern),
            )
        )
    if status == "active":
        query = query.filter_by(is_active=True)
    elif status == "inactive":
        query = query.filter_by(is_active=False)
    devices = query.order_by(USBDevice.last_seen.desc()).all()
    return render_template("devices.html", devices=devices, q=query_text, status=status)


@bp.get("/events")
def events_page():
    events = USBEvent.query.order_by(USBEvent.timestamp.desc()).limit(300).all()
    return render_template("events.html", events=events)


@bp.get("/incidents")
def incidents_page():
    incidents = Incident.query.order_by(Incident.threat_score.desc(), Incident.created_at.desc()).all()
    return render_template("incidents.html", incidents=incidents)


@bp.get("/analytics")
def analytics_page():
    return render_template("analytics.html")


@bp.get("/reports/incidents/<int:incident_id>")
def incident_report(incident_id: int):
    incident = Incident.query.get_or_404(incident_id)
    evidence = Evidence.query.filter_by(
        device_id=incident.device_id, event_id=incident.event_id
    ).all()
    return render_template("incident_report.html", incident=incident, evidence=evidence)


@bp.get("/api/devices")
def api_devices():
    page = _pagination(USBDevice)
    return jsonify({"items": [item.to_dict() for item in page.items], "total": page.total})


@bp.get("/api/events")
def api_events():
    page = _pagination(USBEvent)
    return jsonify({"items": [item.to_dict() for item in page.items], "total": page.total})


@bp.get("/api/incidents")
def api_incidents():
    page = _pagination(Incident)
    return jsonify({"items": [item.to_dict() for item in page.items], "total": page.total})


@bp.get("/api/evidence")
def api_evidence():
    page = _pagination(Evidence)
    return jsonify({"items": [item.to_dict() for item in page.items], "total": page.total})


@bp.get("/api/analytics/summary")
def api_analytics_summary():
    threats = (
        db.session.query(Incident.risk_level, func.count(Incident.id))
        .group_by(Incident.risk_level)
        .all()
    )
    platforms = (
        db.session.query(USBDevice.platform, func.count(USBDevice.id))
        .group_by(USBDevice.platform)
        .all()
    )
    events = (
        db.session.query(USBEvent.event_type, func.count(USBEvent.id))
        .group_by(USBEvent.event_type)
        .all()
    )
    return jsonify(
        {
            "threats": {level or "Unknown": count for level, count in threats},
            "platforms": {platform or "Unknown": count for platform, count in platforms},
            "events": {event_type: count for event_type, count in events},
        }
    )


@bp.post("/api/device")
def api_create_device():
    data = validate_device_payload(request.get_json(silent=True) or {})
    device, is_new = _upsert_device(data)
    event = USBEvent(
        device=device,
        event_type="inserted" if data["is_active"] else "removed",
        username=device.username,
        hostname=device.hostname,
        event_metadata={"source": "device_api"},
    )
    db.session.add(event)
    if not data["is_active"]:
        device.is_active = False
    else:
        _create_incident_if_needed(device, event, known_device=not is_new)
    db.session.commit()
    return jsonify({"device": device.to_dict(), "created": is_new}), 201 if is_new else 200


@bp.post("/api/event")
def api_create_event():
    data = validate_event_payload(request.get_json(silent=True) or {})
    device = None
    if data.get("device_id"):
        device = USBDevice.query.get(data["device_id"])
    event = USBEvent(**data)
    event.device = device
    db.session.add(event)
    if event.sha256 or event.filename or event.path:
        db.session.add(
            Evidence(
                device=device,
                event=event,
                evidence_type="file_activity",
                filename=event.filename,
                path=event.path,
                sha256=event.sha256,
                details={"event_type": event.event_type, **(event.event_metadata or {})},
            )
        )
    if device:
        device.last_seen = datetime.now(timezone.utc)
        device.is_active = event.event_type != "removed"
    _create_incident_if_needed(device, event, known_device=True)
    db.session.commit()
    return jsonify({"event": event.to_dict()}), 201
