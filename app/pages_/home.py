"""Home / Overview screen. Not tied to a single use case - gives context for
all of UC-06..UC-09 plus deployed-model status (FR-06)."""
from __future__ import annotations

import streamlit as st

from app import config, db, model_service
from app.components.status import render_no_model_state
from app.format_utils import format_algorithm_name, format_timestamp


def _text_stat(column, label: str, value: str) -> None:
    """A metric-like stat that wraps instead of truncating, for values
    too long to safely fit in st.metric (which ellipsizes with no wrap)."""
    with column:
        st.caption(label)
        st.markdown(f"#### {value}")


def render() -> None:
    st.title(config.APP_TITLE)
    st.caption(
        "Binary classification of EV battery condition - Failure or No "
        "Failure - to support EV fleet maintenance decisions."
    )

    st.markdown(
        "Electric vehicle batteries degrade and occasionally fail. This "
        "system lets an **EV Maintenance Specialist** manage battery "
        "records, run a Failure / No Failure classification using a model "
        "trained offline by the Data Scientist, and record a maintenance "
        "assessment and recommendation against each result."
    )

    st.divider()
    st.markdown("### Deployed model status")
    status = model_service.get_status()
    if status.deployed:
        metadata = status.bundle["metadata"]
        failure = metadata.get("metrics", {}).get("failure", {})
        features = status.bundle["feature_spec"]["features"]

        c1, c2, c3, c4 = st.columns(4)
        # Algorithm / Trained at are rendered as wrapping text rather than
        # st.metric: st.metric truncates long values with an ellipsis
        # ("logistic_regr...", "2026-11-01T...") instead of wrapping, which
        # loses information. Plain text wraps correctly at any width.
        _text_stat(c1, "Algorithm", format_algorithm_name(metadata.get("algorithm")))
        _text_stat(c2, "Trained at", format_timestamp(metadata.get("trained_at")))
        c3.metric("Features used", len(features))
        c4.metric(
            "Supports probability", "Yes" if metadata.get("supports_probability") else "No"
        )

        st.markdown("**Failure-class metrics** (from the deployed bundle)")
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Precision", f"{failure.get('precision', 0):.3f}")
        m2.metric("Recall", f"{failure.get('recall', 0):.3f}")
        m3.metric("F1-score", f"{failure.get('f1', 0):.3f}")
        m4.metric("Support", failure.get("support", "n/a"))
    else:
        render_no_model_state(status, context="Classification")

    st.divider()
    st.markdown("### Database summary")
    d1, d2 = st.columns(2)
    d1.metric("Battery records", db.count_battery_records())
    d2.metric("Classifications run", db.count_classifications())

    st.divider()
    _render_course_info()


def _render_course_info() -> None:
    info = config.COURSE_INFO
    st.markdown("### Course and project information")
    st.write(info["university_line1"])
    st.write(info["university_line2"])
    st.write(info["faculty"])
    st.write(f"**Course:** {info['course']}")
    st.write(f"**Instructor:** {info['instructor']}")
    st.write(f"**{info['group']}**")
    for student in info["students"]:
        st.write(f"- {student}")
