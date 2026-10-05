from datetime import datetime

from pydantic import BaseModel

from app.schemas.common import Metrics


class ActiveModel(BaseModel):
    run_id: int
    version: str
    algorithm: str
    dataset_name: str
    deployed_at: datetime
    metrics: Metrics
    supports_probability: bool
