"""
Classification result display (FR-14).

Failure vs No Failure must be distinguishable by icon + text label, never
color alone - st.error/st.success already add a colored band, but we always
pair it with an explicit icon and the literal word "FAILURE" / "NO FAILURE"
so the distinction survives in grayscale/colorblind viewing too.
"""
from __future__ import annotations

from typing import Any

import streamlit as st

from app.format_utils import format_algorithm_name, format_timestamp
from app.model_service import PredictionResult


def render_classification_result(
    result: PredictionResult, record: dict[str, Any]
) -> None:
    st.markdown("#### Classification result")
    col_result, col_record = st.columns([2, 3])

    with col_result:
        # icon= already renders the icon once; the message text must not
        # repeat it, or the icon appears doubled on screen.
        if result.prediction == 1:
            st.error("**FAILURE**", icon="⚠️")
        else:
            st.success("**NO FAILURE**", icon="✅")

        if result.probability is not None:
            st.metric("Failure probability", f"{result.probability * 100:.1f}%")
        else:
            st.caption(
                "Probability unavailable: the deployed model does not "
                "support calibrated probability estimates."
            )

        st.caption(
            f"Model: {format_algorithm_name(result.model_algorithm)} "
            f"(trained {format_timestamp(result.model_trained_at)})"
        )

    with col_record:
        st.markdown("**Battery record**")
        st.write(f"Serial: `{record['battery_serial']}`")
        st.write(f"Vehicle ID: `{record['vehicle_id']}`")
        st.caption(f"Record last updated: {format_timestamp(record.get('updated_at'))}")
