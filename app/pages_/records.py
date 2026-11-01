"""Battery Records screen (UC-06, FR-12): search by serial or vehicle id,
list, create, view and update records."""
from __future__ import annotations

from typing import Any, Optional

import streamlit as st

from app import db, model_service
from app.components.forms import render_feature_form
from app.components.status import render_no_model_state
from app.format_utils import format_timestamp

_SELECTED_KEY = "records_selected_id"


def _select_record(record_id: int) -> None:
    st.session_state[_SELECTED_KEY] = record_id


def _clear_selection() -> None:
    st.session_state[_SELECTED_KEY] = None


def _render_record_row(record: dict[str, Any]) -> None:
    c1, c2, c3, c4 = st.columns([3, 3, 3, 2])
    c1.write(f"`{record['battery_serial']}`")
    c2.write(record["vehicle_id"])
    c3.caption(f"Updated {format_timestamp(record['updated_at'])}")
    c4.button(
        "View / Edit",
        key=f"view_{record['id']}",
        on_click=_select_record,
        args=(record["id"],),
        use_container_width=True,
    )


def _render_search_tab() -> None:
    query = st.text_input(
        "Search by battery serial or vehicle ID", placeholder="BAT-10000001 or EV100000"
    )
    results = db.search_battery_records(query) if query.strip() else db.list_battery_records(limit=25)
    label = f"{len(results)} result(s)" if query.strip() else f"{len(results)} most recently updated record(s)"
    st.caption(label)
    if not results:
        st.info("No battery records found.")
        return
    header = st.columns([3, 3, 3, 2])
    header[0].markdown("**Serial**")
    header[1].markdown("**Vehicle ID**")
    header[2].markdown("**Updated**")
    for record in results:
        _render_record_row(record)


def _render_create_tab(bundle_status) -> None:
    if not bundle_status.deployed:
        render_no_model_state(bundle_status, context="Creating a new battery record")
        return

    bundle = bundle_status.bundle
    st.caption(
        "The battery serial must be unique. All 67 model features are "
        "captured; the key ones are shown first."
    )
    with st.form("create_record_form", clear_on_submit=False):
        c1, c2 = st.columns(2)
        serial = c1.text_input("Battery serial *", placeholder="BAT-99999999")
        vehicle_id = c2.text_input("Vehicle ID *", placeholder="EV999999")
        values = render_feature_form(bundle, key_prefix="create")
        submitted = st.form_submit_button("Create record", type="primary")

    if submitted:
        if not serial.strip() or not vehicle_id.strip():
            st.error("Battery serial and vehicle ID are both required.")
            return
        ok, errors = model_service.validate_input(values, bundle["feature_spec"])
        if not ok:
            st.error("Please fix the following before saving:")
            for e in errors:
                st.write(f"- {e}")
            return
        try:
            record_id = db.create_battery_record(serial, vehicle_id, values)
        except ValueError as exc:
            st.error(str(exc))
            return
        st.success(f"Record '{serial}' created (id={record_id}).")
        _select_record(record_id)


def _render_selected_record(bundle_status) -> None:
    record_id = st.session_state.get(_SELECTED_KEY)
    if not record_id:
        return
    record = db.get_battery_record(record_id)
    if record is None:
        st.warning("Selected record no longer exists.")
        _clear_selection()
        return

    st.divider()
    st.markdown(f"### Record: `{record['battery_serial']}`")
    st.caption(
        f"Vehicle ID: {record['vehicle_id']} | "
        f"created {format_timestamp(record['created_at'])}"
    )

    if not bundle_status.deployed:
        render_no_model_state(bundle_status, context="Editing this record's parameters")
        st.markdown("Stored parameters (read-only, raw):")
        st.json(record["parameters"])
        st.button("Close", on_click=_clear_selection)
        return

    bundle = bundle_status.bundle
    with st.form("edit_record_form"):
        new_vehicle_id = st.text_input("Vehicle ID", value=record["vehicle_id"])
        values = render_feature_form(
            bundle, current_values=record["parameters"], key_prefix=f"edit_{record_id}"
        )
        col_save, col_close = st.columns(2)
        save = col_save.form_submit_button("Save changes", type="primary")
        close = col_close.form_submit_button("Close")

    if save:
        ok, errors = model_service.validate_input(values, bundle["feature_spec"])
        if not ok:
            st.error("Please fix the following before saving:")
            for e in errors:
                st.write(f"- {e}")
        else:
            db.update_battery_record(record_id, vehicle_id=new_vehicle_id, parameters=values)
            st.success("Record updated.")
    if close:
        _clear_selection()
        st.rerun()

    history = db.list_classifications_for_record(record_id)
    if history:
        st.markdown(f"**Classification history for this record** ({len(history)})")
        for item in history[:5]:
            icon = "⚠️" if item["prediction"] == 1 else "✅"
            st.write(
                f"{icon} {item['prediction_label']} - "
                f"{format_timestamp(item['created_at'])}"
            )


def render(bundle_status) -> None:
    st.title("Battery Records")
    st.caption("Search, create, view and update battery records (UC-06, FR-12).")

    if _SELECTED_KEY not in st.session_state:
        st.session_state[_SELECTED_KEY] = None

    tab_search, tab_create = st.tabs(["Search / Browse", "Create new record"])
    with tab_search:
        _render_search_tab()
    with tab_create:
        _render_create_tab(bundle_status)

    _render_selected_record(bundle_status)
