from datetime import datetime
from typing import Literal

from pydantic import BaseModel

from app.schemas.common import HealthClass
from app.schemas.vehicles import Battery, Measurement, Vehicle


class UserBatteryOverview(BaseModel):
    vehicle: Vehicle
    battery: Battery
    current_soh: float | None
    health_class: HealthClass | None
    last_checked_at: datetime | None
    soh_change_30d: float | None
    recommendation: str
    history: list[Measurement]


class MaintenanceItem(BaseModel):
    id: int
    title: str
    description: str
    severity: Literal["info", "warning", "critical"]
    due_at: datetime | None
    completed: bool
