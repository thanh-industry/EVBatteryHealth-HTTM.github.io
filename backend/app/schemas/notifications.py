from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict


class Notification(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    type: Literal["degradation", "critical_health", "maintenance_reminder", "system"]
    severity: Literal["info", "warning", "critical"]
    title: str
    body: str
    created_at: datetime
    read_at: datetime | None
