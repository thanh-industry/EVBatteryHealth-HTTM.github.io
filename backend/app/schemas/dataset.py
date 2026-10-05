from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class DatasetOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    filename: str
    row_count: int
    column_count: int
    missing_cells: int
    missing_pct: float
    duplicate_rows: int
    uploaded_at: datetime
    status: Literal["ready", "invalid"]
    message: str | None


class DatasetPreview(BaseModel):
    columns: list[str]
    rows: list[dict]


class ClassDistributionItem(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    class_: Literal["GOOD", "MONITOR", "CRITICAL"] = Field(alias="class")
    count: int


class MissingByColumnItem(BaseModel):
    column: str
    missing: int
    missing_pct: float


class NumericSummaryItem(BaseModel):
    column: str
    min: float
    max: float
    mean: float
    std: float


class SohHistogramBin(BaseModel):
    bin_start: float
    bin_end: float
    count: int


class ExcludedColumnItem(BaseModel):
    column: str
    reason: str


class DataQuality(BaseModel):
    dataset_id: int
    row_count: int
    labelled_rows: int
    dropped_missing_label: int
    duplicate_rows: int
    class_distribution: list[ClassDistributionItem]
    missing_by_column: list[MissingByColumnItem]
    numeric_summary: list[NumericSummaryItem]
    soh_histogram: list[SohHistogramBin]
    excluded_columns: list[ExcludedColumnItem]
