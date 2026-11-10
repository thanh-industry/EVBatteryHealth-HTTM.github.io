"""
Measurement trend across repeated inspections (extends FR-16).

FR-16 requires previous results to be viewable, which the history list
satisfies: it shows what each inspection concluded. It does not show the
direction a battery is moving, which is the question a maintenance specialist
actually asks when deciding whether to act now or at the next service.

Every classification already stores the exact inputs it was given
(classifications.input_snapshot_json), so the data needed for a trend is
captured today and no schema change is required. A series is simply those
snapshots ordered by created_at.

Why three charts and not one
---------------------------
State of Health is a percentage near 80, Capacity Loss a percentage near 17,
and temperature is degrees Celsius near 36. Plotting them on shared axes - or
worse, on two y-axes - would make unrelated quantities look comparable and
invite a reader to compare slopes that have no common meaning. They are
rendered as small multiples: one chart per metric, one series each, each with
its own scale.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

# A trend needs at least two readings. One reading is a point, not a trend,
# and drawing a flat segment through a single value implies a stability the
# data does not support.
MIN_POINTS = 2


@dataclass(frozen=True)
class TrendMetric:
    key: str
    label: str
    unit: str
    # Smallest span the y-axis may cover. Without this the axis auto-fits the
    # observed values, so a 0.1% drift fills the panel and reads as a crisis.
    min_span: float


TREND_METRICS: tuple[TrendMetric, ...] = (
    TrendMetric("state_of_health", "State of Health", "%", 5.0),
    TrendMetric("capacity_loss_percent", "Capacity Loss", "%", 5.0),
    TrendMetric("cell_temperature_avg", "Cell Temp (avg)", "°C", 4.0),
)


@dataclass
class TrendPoint:
    at: str
    value: float


@dataclass
class TrendSeries:
    metric: TrendMetric
    points: list[TrendPoint]

    @property
    def latest(self) -> float:
        return self.points[-1].value

    @property
    def domain(self) -> tuple[float, float]:
        """y-axis range: the observed values, widened to the metric's minimum
        span and then padded, so the slope on screen reflects the size of the
        change rather than the resolution of the data."""
        values = [p.value for p in self.points]
        low, high = min(values), max(values)
        span = high - low
        if span < self.metric.min_span:
            mid = (high + low) / 2.0
            low, high = mid - self.metric.min_span / 2.0, mid + self.metric.min_span / 2.0
            span = self.metric.min_span
        pad = span * 0.12
        return (low - pad, high + pad)


def _coerce(value: Any) -> Optional[float]:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if number != number or number in (float("inf"), float("-inf")):  # NaN/inf
        return None
    return number


def build_trends(
    classifications: list[dict[str, Any]],
    metrics: tuple[TrendMetric, ...] = TREND_METRICS,
) -> list[TrendSeries]:
    """Build one series per metric from a record's classifications.

    `classifications` may arrive in any order (db returns newest first); they
    are sorted oldest-first here so the chart reads left to right in time.
    A metric missing from the stored snapshots is skipped rather than drawn
    with gaps, which keeps this working if a different dataset is ever
    deployed.
    """
    ordered = sorted(
        classifications,
        key=lambda c: (str(c.get("created_at") or ""), int(c.get("id") or 0)),
    )

    series: list[TrendSeries] = []
    for metric in metrics:
        points: list[TrendPoint] = []
        for item in ordered:
            snapshot = item.get("input_snapshot") or {}
            value = _coerce(snapshot.get(metric.key))
            if value is None:
                continue
            points.append(TrendPoint(at=str(item.get("created_at") or ""), value=value))
        if len(points) >= MIN_POINTS:
            series.append(TrendSeries(metric=metric, points=points))
    return series


def has_enough_history(classifications: list[dict[str, Any]]) -> bool:
    return len(classifications) >= MIN_POINTS
