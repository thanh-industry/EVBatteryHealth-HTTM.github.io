"""
Tests for chart construction.

These assert the chart SPECIFICATION rather than pixels: that the diverging
palette is the colour-vision-checked pair, that the trend axis uses the
widened domain rather than auto-fitting, and that both charts build without
raising for realistic inputs.
"""
from __future__ import annotations

from app import charts, explain, model_service, trend


def _series():
    readings = [
        {"id": 1, "created_at": "2026-03-01T10:00:00+00:00",
         "input_snapshot": {"state_of_health": 88.4}},
        {"id": 2, "created_at": "2026-07-01T10:00:00+00:00",
         "input_snapshot": {"state_of_health": 85.9}},
    ]
    return trend.build_trends(readings)[0]


def test_attribution_chart_builds_and_is_serialisable(small_bundle):
    values = model_service.build_default_values(small_bundle)
    attribution = explain.compute_attribution(small_bundle, values)
    chart = charts.attribution_chart(attribution)
    spec = chart.to_dict()
    assert spec["layer"], "expected a layered chart"


def test_attribution_uses_the_cvd_checked_diverging_pair(small_bundle):
    values = model_service.build_default_values(small_bundle)
    attribution = explain.compute_attribution(small_bundle, values)
    spec = charts.attribution_chart(attribution).to_dict()

    colors = _collect(spec, "range")
    assert [charts.COLOR_FAILURE, charts.COLOR_OK] in colors, (
        "the Failure/No-Failure pair must stay the validated colours"
    )


def test_attribution_frame_prints_a_signed_value_for_every_row(small_bundle):
    """Colour is never the only signal: each row carries its signed number."""
    values = model_service.build_default_values(small_bundle)
    attribution = explain.compute_attribution(small_bundle, values)
    frame = charts.attribution_frame(attribution)

    assert len(frame) == len(attribution.top)
    assert set(frame["direction"]) <= {charts.TOWARD_FAILURE, charts.TOWARD_OK}
    assert frame["contribution"].notna().all()


def test_trend_chart_uses_the_widened_domain_not_an_auto_fit():
    series = _series()
    spec = charts.trend_chart(series).to_dict()
    low, high = series.domain

    domains = _collect(spec, "domain")
    assert [low, high] in domains, (
        "the y scale must use TrendSeries.domain so a small change is not "
        "exaggerated by an auto-fitted axis"
    )


def test_trend_chart_builds_for_every_metric():
    readings = [
        {"id": 1, "created_at": "2026-03-01T10:00:00+00:00",
         "input_snapshot": {"state_of_health": 88.4, "capacity_loss_percent": 11.2,
                            "cell_temperature_avg": 33.1}},
        {"id": 2, "created_at": "2026-07-01T10:00:00+00:00",
         "input_snapshot": {"state_of_health": 85.9, "capacity_loss_percent": 13.7,
                            "cell_temperature_avg": 34.2}},
    ]
    built = trend.build_trends(readings)
    assert len(built) == 3
    for item in built:
        assert charts.trend_chart(item).to_dict()["layer"]


def _collect(node, key):
    """Every value stored under `key` anywhere in a Vega-Lite spec."""
    found = []
    if isinstance(node, dict):
        for k, v in node.items():
            if k == key:
                found.append(v)
            found.extend(_collect(v, key))
    elif isinstance(node, list):
        for item in node:
            found.extend(_collect(item, key))
    return found


def test_attribution_never_drops_feature_labels(small_bundle):
    """Regression: Vega hides colliding axis labels by default, which left
    bars with no feature name beside them - the chart showed 8 bars and 4
    labels. Every band must stay labelled."""
    values = model_service.build_default_values(small_bundle)
    attribution = explain.compute_attribution(small_bundle, values)
    spec = charts.attribution_chart(attribution).to_dict()

    overlaps = _collect(spec, "labelOverlap")
    assert overlaps, "no labelOverlap setting found on the attribution chart"
    assert all(v is False for v in overlaps), (
        f"labelOverlap must be False on every axis, got {overlaps}"
    )


def test_attribution_height_scales_with_row_count(small_bundle):
    """A fixed total height has to absorb the legend and x-axis, squeezing
    the bands. Height must be per-band so eight rows stay readable."""
    values = model_service.build_default_values(small_bundle)
    attribution = explain.compute_attribution(small_bundle, values)
    spec = charts.attribution_chart(attribution).to_dict()

    heights = [h for h in _collect(spec, "height") if isinstance(h, (int, float))]
    assert heights, f"expected a pixel height, got {_collect(spec, 'height')}"
    # Vega-Lite ignores step sizing on a layered view, so the height must be
    # explicit pixels AND must grow with the number of rows.
    assert max(heights) >= 26 * len(attribution.top), (
        f"height {max(heights)} too small for {len(attribution.top)} rows"
    )
