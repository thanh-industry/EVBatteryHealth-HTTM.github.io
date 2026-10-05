from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.security import require_role
from app.db.session import get_db
from app.models.diagnostic import Diagnostic
from app.models.user import User
from app.schemas.diagnostics import (
    Diagnostic as DiagnosticSchema,
    DiagnosticCreateRequest,
    DiagnosticSummary,
)
from app.services import prediction_service, vehicle_service

router = APIRouter(prefix="/api/diagnostics", tags=["diagnostics"])

_require_technician = require_role("technician")

_RECENT_LIMIT = 10


@router.post("", response_model=DiagnosticSchema, status_code=201)
def create_diagnostic(
    body: DiagnosticCreateRequest,
    db: Session = Depends(get_db),
    user: User = Depends(_require_technician),
) -> DiagnosticSchema:
    vehicle = vehicle_service.find_by_vehicle_or_battery_code(db, body.code)
    if vehicle is None:
        raise HTTPException(status_code=404, detail=f"No vehicle or battery matching '{body.code}' found.")

    diagnostic = prediction_service.run_diagnostic(db, vehicle, vehicle.battery, user, body.notes)
    return DiagnosticSchema(**prediction_service.diagnostic_to_schema(db, diagnostic))


@router.get("", response_model=list[DiagnosticSchema])
def list_diagnostics(
    code: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db),
    _user: User = Depends(_require_technician),
) -> list[DiagnosticSchema]:
    query = db.query(Diagnostic)
    if code:
        vehicle = vehicle_service.find_by_vehicle_or_battery_code(db, code)
        if vehicle is None:
            return []
        query = query.filter(Diagnostic.vehicle_id == vehicle.id)
    diagnostics = query.order_by(Diagnostic.created_at.desc()).limit(limit).all()
    return [DiagnosticSchema(**prediction_service.diagnostic_to_schema(db, d)) for d in diagnostics]


@router.get("/summary", response_model=DiagnosticSummary)
def get_summary(
    db: Session = Depends(get_db), _user: User = Depends(_require_technician)
) -> DiagnosticSummary:
    all_diagnostics = db.query(Diagnostic).order_by(Diagnostic.created_at.desc()).all()

    today = datetime.now(timezone.utc).date()
    today_count = sum(1 for d in all_diagnostics if d.created_at.date() == today)
    good_count = sum(1 for d in all_diagnostics if d.predicted_class == "GOOD")
    monitor_count = sum(1 for d in all_diagnostics if d.predicted_class == "MONITOR")
    critical_count = sum(1 for d in all_diagnostics if d.predicted_class == "CRITICAL")

    recent = [
        DiagnosticSchema(**prediction_service.diagnostic_to_schema(db, d))
        for d in all_diagnostics[:_RECENT_LIMIT]
    ]

    return DiagnosticSummary(
        today_count=today_count,
        good_count=good_count,
        monitor_count=monitor_count,
        critical_count=critical_count,
        recent=recent,
    )
