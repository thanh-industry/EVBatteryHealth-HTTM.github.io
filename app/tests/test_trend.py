"""
Tests for the measurement-trend series builder.

The behaviours that matter: a single reading is never drawn as a trend, the
series reads oldest-first regardless of how the database returned it, and the
y-axis never auto-fits so tightly that a negligible change looks dramatic.
"""
from __future__ import annotations

import pytest

from app import trend


def _classification(created_at: str, **snapshot) -> dict:
    return {
        "id": abs(hash(created_at)) % 100000,
        "created_at": created_at,
        "input_snapshot": snapshot,
    }


def _three_readings() -> list[dict]:
    return [
        _classification("2026-03-01T10:00:00+00:00", state_of_health=88.4,
                        capacity_loss_percent=11.2, cell_temperature_avg=33.1),
        _classification("2026-07-01T10:00:00+00:00", state_of_health=85.9,
                        capacity_loss_percent=13.7, cell_temperature_avg=34.2),
        _classification("2026-11-01T10:00:00+00:00", state_of_health=82.1,
                        capacity_loss_percent=16.8, cell_temperature_avg=35.7),
    ]


def test_builds_one_series_per_metric():
    series = trend.build_trends(_three_readings())
    assert [s.metric.key for s in series] == [
        "state_of_health",
        "capacity_loss_percent",
        "cell_temperature_avg",
    ]
    assert all(len(s.points) == 3 for s in series)


def test_series_is_ordered_oldest_first_even_when_input_is_newest_first():
    """db.list_classifications_for_record returns newest first; a chart drawn
    in that order would show the battery improving over time."""
    newest_first = list(reversed(_three_readings()))
    series = trend.build_trends(newest_first)
    soh = next(s for s in series if s.metric.key == "state_of_health")

    assert [p.value for p in soh.points] == [88.4, 85.9, 82.1]
    assert soh.latest == 82.1


def test_single_reading_produces_no_series():
    """One point is not a trend. Drawing it would imply a stability the data
    does not support."""
    assert trend.build_trends(_three_readings()[:1]) == []
    assert not trend.has_enough_history(_three_readings()[:1])
    assert trend.has_enough_history(_three_readings()[:2])


def test_no_classifications_produces_no_series():
    assert trend.build_trends([]) == []
    assert not trend.has_enough_history([])


def test_metric_absent_from_snapshots_is_skipped_not_drawn_with_gaps():
    readings = [
        _classification("2026-03-01T10:00:00+00:00", state_of_health=88.4),
        _classification("2026-07-01T10:00:00+00:00", state_of_health=85.9),
    ]
    series = trend.build_trends(readings)
    assert [s.metric.key for s in series] == ["state_of_health"]


def test_unparseable_values_are_dropped():
    readings = [
        _classification("2026-03-01T10:00:00+00:00", state_of_health=88.4),
        _classification("2026-05-01T10:00:00+00:00", state_of_health=None),
        _classification("2026-07-01T10:00:00+00:00", state_of_health="n/a"),
        _classification("2026-09-01T10:00:00+00:00", state_of_health=85.9),
    ]
    series = trend.build_trends(readings)
    soh = next(s for s in series if s.metric.key == "state_of_health")
    assert [p.value for p in soh.points] == [88.4, 85.9]


def test_domain_widens_so_a_negligible_change_does_not_fill_the_chart():
    """Two readings 0.02 apart must not render as a dramatic slope."""
    readings = [
        _classification("2026-03-01T10:00:00+00:00", state_of_health=82.10),
        _classification("2026-07-01T10:00:00+00:00", state_of_health=82.12),
    ]
    soh = next(
        s for s in trend.build_trends(readings) if s.metric.key == "state_of_health"
    )
    low, high = soh.domain
    assert high - low >= soh.metric.min_span
    assert low < 82.10 and high > 82.12


def test_domain_tracks_real_spread_when_it_exceeds_the_minimum_span():
    readings = [
        _classification("2026-03-01T10:00:00+00:00", state_of_health=95.0),
        _classification("2026-07-01T10:00:00+00:00", state_of_health=60.0),
    ]
    soh = next(
        s for s in trend.build_trends(readings) if s.metric.key == "state_of_health"
    )
    low, high = soh.domain
    assert low < 60.0 and high > 95.0
    assert high - low == pytest.approx(35.0 * 1.24, rel=1e-6)
