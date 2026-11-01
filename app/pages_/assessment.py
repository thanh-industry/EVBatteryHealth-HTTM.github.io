"""Maintenance Assessment screen (UC-08, FR-15): attach an assessment and
recommendation to a classification result."""
from __future__ import annotations

import streamlit as st

from app import db
from app.format_utils import format_algorithm_name, format_timestamp


def _pending_classifications() -> list[dict]:
    history = db.list_classification_history(limit=200)
    return [h for h in history if h["assessment_id"] is None]


def render() -> None:
    st.title("Maintenance Assessment")
    st.caption(
        "Record a maintenance assessment and recommendation for a "
        "classification result (UC-08, FR-15)."
    )

    pending = _pending_classifications()
    if not pending:
        if db.count_classifications() == 0:
            st.info(
                "No classifications have been run yet. Go to Run "
                "Classification first, then come back here to record an "
                "assessment."
            )
        else:
            st.success("Every classification already has a maintenance assessment.")
        return

    def _fmt(item: dict) -> str:
        icon = "Failure" if item["prediction"] == 1 else "No Failure"
        return (
            f"{item['battery_serial']} / {item['vehicle_id']} - {icon} "
            f"- {format_timestamp(item['classified_at'])}"
        )

    labels = {_fmt(item): item for item in pending}
    choice = st.selectbox("Classification awaiting assessment", list(labels.keys()))
    item = labels[choice]

    st.markdown("#### Classification result")
    c1, c2, c3 = st.columns(3)
    icon = "⚠️" if item["prediction"] == 1 else "✅"
    c1.metric("Result", f"{icon} {item['prediction_label']}")
    c2.metric(
        "Probability",
        f"{item['probability'] * 100:.1f}%" if item["probability"] is not None else "n/a",
    )
    c3.metric("Model", format_algorithm_name(item["model_algorithm"]))

    st.markdown("#### Assessment")
    with st.form("assessment_form"):
        assessment = st.text_area(
            "Assessment *",
            placeholder="e.g. Elevated internal resistance and thermal risk "
            "consistent with the Failure prediction; cell inspection recommended.",
            height=100,
        )
        recommendation = st.text_area(
            "Recommendation *",
            placeholder="e.g. Schedule battery pack inspection within 7 days; "
            "monitor cell temperature in the interim.",
            height=100,
        )
        assessed_by = st.text_input(
            "Assessed by", placeholder="e.g. EV Maintenance Specialist name"
        )
        submitted = st.form_submit_button("Save assessment", type="primary")

    if submitted:
        if not assessment.strip() or not recommendation.strip():
            st.error("Both assessment and recommendation are required.")
            return
        try:
            db.create_assessment(
                classification_id=item["classification_id"],
                assessment=assessment,
                recommendation=recommendation,
                assessed_by=assessed_by.strip() or None,
            )
        except ValueError as exc:
            st.error(str(exc))
            return
        st.success("Assessment saved.")
        st.rerun()
