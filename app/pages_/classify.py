"""Run Classification screen (UC-07, FR-13, FR-14): select a record, edit
its parameters, validate against feature_spec (FR-07), classify (FR-08),
and show Failure / No Failure prominently with the record (FR-14)."""
from __future__ import annotations

import streamlit as st

from app import db, model_service
from app.components.forms import render_feature_form
from app.components.results import render_classification_result
from app.components.status import render_no_model_state

_SELECTED_KEY = "classify_selected_id"
_LAST_RESULT_KEY = "classify_last_result"


def _select(record_id: int) -> None:
    st.session_state[_SELECTED_KEY] = record_id
    st.session_state[_LAST_RESULT_KEY] = None


def _clear() -> None:
    st.session_state[_SELECTED_KEY] = None
    st.session_state[_LAST_RESULT_KEY] = None


def _render_picker() -> None:
    st.markdown("#### 1. Select a battery record")
    query = st.text_input(
        "Search by battery serial or vehicle ID",
        placeholder="BAT-10000001 or EV100000",
        key="classify_search",
    )
    results = db.search_battery_records(query) if query.strip() else db.list_battery_records(limit=10)
    if not results:
        st.info(
            "No matching battery records. Create one on the Battery Records "
            "screen first."
        )
        return
    for record in results:
        c1, c2, c3 = st.columns([3, 3, 2])
        c1.write(f"`{record['battery_serial']}`")
        c2.write(record["vehicle_id"])
        c3.button(
            "Select",
            key=f"select_{record['id']}",
            on_click=_select,
            args=(record["id"],),
            use_container_width=True,
        )


def _render_classification(bundle_status) -> None:
    record_id = st.session_state.get(_SELECTED_KEY)
    record = db.get_battery_record(record_id)
    if record is None:
        st.warning("Selected record no longer exists.")
        _clear()
        return

    bundle = bundle_status.bundle
    st.markdown("#### 2. Review parameters and classify")
    st.caption(
        f"Battery `{record['battery_serial']}` / vehicle `{record['vehicle_id']}`. "
        "Edit any parameter below; saving a classification also updates the "
        "stored record with these values."
    )
    st.button("Choose a different record", on_click=_clear)

    with st.form("classify_form"):
        values = render_feature_form(
            bundle, current_values=record["parameters"], key_prefix=f"classify_{record_id}"
        )
        submitted = st.form_submit_button("Classify", type="primary")

    if not submitted:
        last = st.session_state.get(_LAST_RESULT_KEY)
        if last is not None:
            render_classification_result(last, record)
        return

    ok, errors = model_service.validate_input(values, bundle["feature_spec"])
    if not ok:
        st.error("Input validation failed - fix the following and try again:")
        for e in errors:
            st.write(f"- {e}")
        st.session_state[_LAST_RESULT_KEY] = None
        return

    result = model_service.predict(bundle, values)
    db.create_classification(
        battery_record_id=record_id,
        prediction=result.prediction,
        prediction_label=result.label,
        probability=result.probability,
        model_algorithm=result.model_algorithm,
        model_trained_at=result.model_trained_at,
        input_snapshot=values,
    )
    db.update_battery_record(record_id, parameters=values)

    st.session_state[_LAST_RESULT_KEY] = result
    record = db.get_battery_record(record_id)
    render_classification_result(result, record)
    st.info(
        "Result saved. Go to Maintenance Assessment to record an assessment "
        "and recommendation for this classification."
    )


def render(bundle_status) -> None:
    st.title("Run Classification")
    st.caption(
        "Select a battery record, confirm its parameters, and classify it "
        "as Failure or No Failure (UC-07, FR-13, FR-14)."
    )

    if not bundle_status.deployed:
        render_no_model_state(bundle_status, context="Running a classification")
        return

    if _SELECTED_KEY not in st.session_state:
        st.session_state[_SELECTED_KEY] = None
    if _LAST_RESULT_KEY not in st.session_state:
        st.session_state[_LAST_RESULT_KEY] = None

    if st.session_state[_SELECTED_KEY] is None:
        _render_picker()
    else:
        _render_classification(bundle_status)
