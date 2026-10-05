from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from app.core.config import settings
from app.schemas.common import ConfusionMatrix, FeatureImportanceItem, Metrics

Algorithm = Literal["svm", "random_forest", "logistic_regression"]
RunStatus = Literal["pending", "running", "completed", "failed"]


class TrainingRequest(BaseModel):
    dataset_id: int
    algorithm: Algorithm
    test_size: float = Field(
        default=settings.DEFAULT_TEST_SIZE, ge=settings.MIN_TEST_SIZE, le=settings.MAX_TEST_SIZE
    )
    params: dict[str, float | str | bool] | None = None


class TrainingRunOut(BaseModel):
    id: int
    dataset_id: int
    dataset_name: str
    algorithm: Algorithm
    params: dict
    test_size: float
    status: RunStatus
    error: str | None
    started_at: datetime
    completed_at: datetime | None
    duration_seconds: float | None
    train_rows: int | None
    test_rows: int | None
    metrics: Metrics | None
    confusion_matrix: ConfusionMatrix | None
    feature_importance: list[FeatureImportanceItem] | None
    supports_probability: bool
    is_deployed: bool
    version: str | None
