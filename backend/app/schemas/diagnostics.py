from datetime import datetime

from pydantic import BaseModel

from app.schemas.common import ClassProbability, HealthClass


class DiagnosticCreateRequest(BaseModel):
    code: str
    notes: str | None = None


class Diagnostic(BaseModel):
    id: int
    vehicle_code: str
    battery_serial: str
    created_at: datetime
    soh: float
    predicted_class: HealthClass
    confidence: float | None
    class_probabilities: list[ClassProbability] | None
    model_version: str
    model_algorithm: str
    technician_name: str | None
    recommendation: str
    notes: str | None


class DiagnosticSummary(BaseModel):
    today_count: int
    good_count: int
    monitor_count: int
    critical_count: int
    recent: list[Diagnostic]
