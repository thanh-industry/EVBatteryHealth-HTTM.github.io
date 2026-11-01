"""Classification History screen (UC-09, FR-16): previous results with
their assessments, filterable by serial/vehicle, newest first."""
from __future__ import annotations

import streamlit as st

from app import db
from app.format_utils import format_algorithm_name, format_timestamp


def render() -> None:
    st.title("Classification History")
    st.caption(
        "Previous classification results and their maintenance assessments, "
        "newest first (UC-09, FR-16)."
    )

    c1, c2 = st.columns(2)
    serial_filter = c1.text_input("Filter by battery serial", placeholder="BAT-10000001")
    vehicle_filter = c2.text_input("Filter by vehicle ID", placeholder="EV100000")

    history = db.list_classification_history(
        serial=serial_filter or None, vehicle_id=vehicle_filter or None
    )

    st.caption(f"{len(history)} classification(s)")
    if not history:
        st.info("No classification history matches these filters.")
        return

    for item in history:
        icon = "⚠️" if item["prediction"] == 1 else "✅"
        title = (
            f"{icon} {item['prediction_label']} - {item['battery_serial']} / "
            f"{item['vehicle_id']} - {format_timestamp(item['classified_at'])}"
        )
        with st.expander(title):
            c1, c2, c3 = st.columns(3)
            c1.metric("Result", f"{icon} {item['prediction_label']}")
            c2.metric(
                "Probability",
                f"{item['probability'] * 100:.1f}%"
                if item["probability"] is not None
                else "unavailable",
            )
            c3.metric("Model", format_algorithm_name(item["model_algorithm"]))
            st.caption(f"Model trained at: {format_timestamp(item['model_trained_at'])}")

            st.markdown("**Maintenance assessment**")
            if item["assessment_id"] is None:
                st.info("No assessment has been recorded for this classification yet.")
            else:
                st.write(f"Assessment: {item['assessment']}")
                st.write(f"Recommendation: {item['recommendation']}")
                assessor = item["assessed_by"] or "unspecified"
                st.caption(
                    f"Assessed by {assessor} on {format_timestamp(item['assessed_at'])}"
                )
