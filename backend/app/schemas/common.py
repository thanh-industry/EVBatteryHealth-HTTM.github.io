from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

HealthClass = Literal["GOOD", "MONITOR", "CRITICAL"]


class PerClassMetric(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    class_: str = Field(alias="class")
    precision: float
    recall: float
    f1: float
    support: int


class Metrics(BaseModel):
    accuracy: float
    precision_macro: float
    recall_macro: float
    f1_macro: float
    per_class: list[PerClassMetric]


class ConfusionMatrix(BaseModel):
    labels: list[str]
    matrix: list[list[int]]


class FeatureImportanceItem(BaseModel):
    feature: str
    importance: float


class ClassProbability(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    class_: str = Field(alias="class")
    probability: float
