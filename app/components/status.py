"""
Deployed-model status presentation (FR-06).

The text-building logic is kept in plain functions (no `st` calls) so it can
be unit tested without a running Streamlit script context. The `render_*`
functions are thin wrappers that only call into Streamlit.
"""
from __future__ import annotations

import streamlit as st

from app.model_service import BundleStatus


def no_model_message(status: BundleStatus) -> str:
    """Human-readable explanation of why classification is unavailable.
    Never raises, regardless of why the model failed to load."""
    reason = status.error or "The model is not available."
    return (
        "No classification model is deployed.\n\n"
        f"Reason: {reason}\n\n"
        "This is expected before Stage 2 (Model Deployment) has run. "
        "The Software Developer must deploy a validated model bundle first:\n\n"
        "    python deployment/deploy_model.py "
        "--bundle ml_pipeline/artifacts/model_bundle.joblib --target models/\n\n"
        "Then verify it with:\n\n"
        "    python deployment/verify_model.py"
    )


def render_no_model_state(status: BundleStatus, context: str = "This screen") -> None:
    st.warning(f"{context} requires a deployed model.", icon="⚠️")
    st.code(no_model_message(status), language="text")


def render_model_badge(status: BundleStatus) -> None:
    if status.deployed:
        algo = status.bundle["metadata"].get("algorithm", "unknown")
        st.sidebar.success(f"Model deployed: {algo}", icon="✅")
    else:
        st.sidebar.error("No model deployed", icon="⚠️")
