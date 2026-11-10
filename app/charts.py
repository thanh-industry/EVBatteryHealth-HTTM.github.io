"""
Chart construction for the application.

Kept free of Streamlit so each chart can be built and asserted in a plain
pytest, and so the chart specification lives in one place rather than being
inlined into page code.

Colour decisions follow the project's design tokens:
  failure  #B91C1C   no-failure  #047857   measurement series  #1D4ED8

The failure/no-failure pair was checked for colour-vision deficiency rather
than chosen by eye (OKLab dE 8.4 under deuteranopia, 27.8 under normal
vision). Colour is never the only signal in either chart: the attribution
chart prints the signed value and a legend, and the trend charts carry one
series each with the metric named in the title.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

import altair as alt
import pandas as pd

if TYPE_CHECKING:  # pragma: no cover
    from app.explain import Attribution
    from app.trend import TrendSeries

COLOR_FAILURE = "#B91C1C"
COLOR_OK = "#047857"
COLOR_SERIES = "#1D4ED8"
COLOR_AXIS = "#6B7280"
COLOR_GRID = "#E9EDF3"

TOWARD_FAILURE = "Pushes toward Failure"
TOWARD_OK = "Pushes toward No Failure"


def attribution_frame(attribution: "Attribution") -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "feature": c.label,
                "value": "" if c.value is None else str(c.value),
                "contribution": c.contribution,
                "direction": TOWARD_FAILURE if c.toward_failure else TOWARD_OK,
            }
            for c in attribution.top
        ]
    )


def attribution_chart(attribution: "Attribution") -> alt.LayerChart:
    """Diverging bar chart of per-feature log-odds contributions.

    The data's job here is polarity - which way each input pushed this one
    prediction - so the form is two hues around a neutral zero axis, not a
    single ranked ramp. Bars are ordered by magnitude, largest first.
    """
    frame = attribution_frame(attribution)
    order = frame.reindex(
        frame["contribution"].abs().sort_values(ascending=False).index
    )["feature"].tolist()

    limit = attribution.max_abs * 1.35  # headroom so value labels are not clipped

    base = alt.Chart(frame)

    bars = base.mark_bar(height=12, cornerRadius=3).encode(
        x=alt.X(
            "contribution:Q",
            title="Contribution to log-odds of Failure",
            scale=alt.Scale(domain=[-limit, limit]),
            axis=alt.Axis(grid=True, gridColor=COLOR_GRID, labelColor=COLOR_AXIS,
                          titleColor=COLOR_AXIS),
        ),
        y=alt.Y("feature:N", title=None, sort=order,
                # labelOverlap must be off: Vega silently drops colliding
                # labels, which leaves bars with no feature name against them
                # and makes the chart unreadable. The Step height below
                # guarantees each band is tall enough to label.
                axis=alt.Axis(labelLimit=220, labelColor="#111827", domain=False,
                              ticks=False, labelOverlap=False)),
        color=alt.Color(
            "direction:N",
            title=None,
            scale=alt.Scale(
                domain=[TOWARD_FAILURE, TOWARD_OK],
                range=[COLOR_FAILURE, COLOR_OK],
            ),
            legend=alt.Legend(orient="top", direction="horizontal", offset=4),
        ),
        tooltip=[
            alt.Tooltip("feature:N", title="Feature"),
            alt.Tooltip("value:N", title="Value used"),
            alt.Tooltip("contribution:Q", title="Contribution", format="+.4f"),
        ],
    )

    # The signed number is printed next to every bar, so the direction is
    # readable without relying on hue at all.
    labels = base.mark_text(
        align="left", baseline="middle", dx=6, fontSize=11, color="#4B5563"
    ).transform_calculate(
        anchor="datum.contribution >= 0 ? datum.contribution : 0"
    ).encode(
        x=alt.X("anchor:Q", scale=alt.Scale(domain=[-limit, limit])),
        y=alt.Y("feature:N", sort=order,
                axis=alt.Axis(labelOverlap=False)),
        text=alt.Text("contribution:Q", format="+.2f"),
    )

    zero = alt.Chart(pd.DataFrame({"x": [0.0]})).mark_rule(
        color="#C9D1DD", strokeWidth=1
    ).encode(x="x:Q")

    # Height is the PLOT AREA height and must be given in pixels: Vega-Lite
    # ignores step-based sizing on a layered view (it is only supported for
    # single views), so alt.Step here would silently do nothing and the bands
    # would collapse to ~15px, at which point Vega starts dropping the
    # feature labels. 26px per row keeps every band labelled.
    # width="container" rather than Streamlit's use_container_width: that flag
    # makes Vega autosize "fit", which rescales the whole view to the
    # container and silently overrides the height below, squeezing eight rows
    # into ~17px bands. Letting Vega own the width and fixing the height keeps
    # the chart responsive AND correctly proportioned.
    return (
        alt.layer(zero, bars, labels)
        .properties(width="container", height=26 * max(len(frame), 1))
        .configure_view(stroke=None)
    )


def trend_chart(series: "TrendSeries") -> alt.LayerChart:
    """One metric over successive inspections.

    One series per chart by design - see app/trend.py for why these are small
    multiples rather than a single combined chart. A single-series chart needs
    no legend: the panel title names it.
    """
    frame = pd.DataFrame(
        [{"at": pd.to_datetime(p.at, errors="coerce", utc=True), "value": p.value}
         for p in series.points]
    )
    low, high = series.domain
    unit = series.metric.unit

    base = alt.Chart(frame)
    line = base.mark_line(strokeWidth=2, color=COLOR_SERIES, point=False).encode(
        x=alt.X("at:T", title=None,
                axis=alt.Axis(format="%d %b", labelColor=COLOR_AXIS, grid=False,
                              tickCount=min(len(frame), 4))),
        y=alt.Y("value:Q", title=None, scale=alt.Scale(domain=[low, high]),
                axis=alt.Axis(labelColor=COLOR_AXIS, gridColor=COLOR_GRID,
                              tickCount=4)),
    )
    points = base.mark_point(
        filled=True, size=55, color=COLOR_SERIES, opacity=1
    ).encode(
        x=alt.X("at:T"),
        y=alt.Y("value:Q", scale=alt.Scale(domain=[low, high])),
        tooltip=[
            alt.Tooltip("at:T", title="Inspected", format="%d %b %Y %H:%M"),
            alt.Tooltip("value:Q", title=f"{series.metric.label} ({unit})",
                        format=".2f"),
        ],
    )
    return (
        alt.layer(line, points)
        .properties(width="container", height=150)
        .configure_view(stroke=None)
    )
