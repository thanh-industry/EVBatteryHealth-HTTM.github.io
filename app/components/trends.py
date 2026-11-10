"""
Measurement-trend panel for a battery record.

Renders one small-multiple chart per metric, or - when the record has fewer
than two stored classifications - the "awaiting repeat inspections" state.
That state is normal for a newly added battery, not an error, so it uses a
neutral informational treatment rather than a warning.
"""
from __future__ import annotations

from typing import Any

import streamlit as st

from app import trend
from app.charts import trend_chart


def render_measurement_trend(classifications: list[dict[str, Any]]) -> None:
    st.markdown("#### Measurement trend")

    series = trend.build_trends(classifications)
    if not series:
        st.info(
            f"Not enough readings yet. This record has "
            f"{len(classifications)} stored "
            f"{'classification' if len(classifications) == 1 else 'classifications'}; "
            f"a trend needs at least {trend.MIN_POINTS}. Run a classification "
            "again after the next inspection and State of Health, Capacity "
            "Loss and temperature will be charted here.",
            icon="📈",
        )
        return

    st.caption(
        "Condition across recorded inspections, taken from the inputs stored "
        "with each classification. Each metric is charted separately because "
        "they carry different units and scales."
    )

    columns = st.columns(len(series))
    for column, item in zip(columns, series):
        with column:
            st.metric(
                f"{item.metric.label} ({item.metric.unit})",
                f"{item.latest:.2f}",
                delta=f"{item.latest - item.points[0].value:+.2f}",
                delta_color="off",
            )
            st.altair_chart(trend_chart(item), theme=None)
