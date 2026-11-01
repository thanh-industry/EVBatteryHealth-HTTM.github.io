"""
UI smoke tests: every screen must render without raising even when no model
is deployed (a real, expected state per SPEC_CONTRACT.md stage 2/3, not an
error). Streamlit's `st.*` calls are harmless outside a running app context
(they log a "missing ScriptRunContext" warning rather than raising), so
calling render() directly here is a legitimate way to prove the page logic
itself never crashes on this path.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from app import config, db
from app.model_service import BundleStatus


@pytest.fixture()
def no_model_status() -> BundleStatus:
    return BundleStatus(
        deployed=False,
        bundle=None,
        error="No model is deployed yet. Run deployment/deploy_model.py.",
        path=Path("models/model_bundle.joblib"),
    )


@pytest.fixture(autouse=True)
def _isolated_db(tmp_path, monkeypatch):
    test_db_path = tmp_path / "smoke.db"
    monkeypatch.setattr(config, "DB_PATH", test_db_path)
    db.init_db()
    return test_db_path


def test_home_render_no_model_does_not_raise():
    from app.pages_ import home

    home.render()


def test_records_render_no_model_does_not_raise(no_model_status):
    from app.pages_ import records

    records.render(no_model_status)


def test_classify_render_no_model_does_not_raise(no_model_status):
    from app.pages_ import classify

    classify.render(no_model_status)


def test_assessment_render_empty_db_does_not_raise():
    from app.pages_ import assessment

    assessment.render()


def test_history_render_empty_db_does_not_raise():
    from app.pages_ import history

    history.render()


def test_records_render_with_existing_record_and_no_model(no_model_status):
    """A record created while a model was deployed must still display
    (read-only) after the model is removed/corrupted, not crash."""
    from app.pages_ import records

    db.create_battery_record("BAT-SMOKE", "EV-SMOKE", {"battery_health_percent": 77.0})
    import streamlit as st

    st.session_state["records_selected_id"] = 1
    records.render(no_model_status)
