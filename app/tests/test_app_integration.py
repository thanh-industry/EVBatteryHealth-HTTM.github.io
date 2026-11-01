"""
Full-app integration test using Streamlit's own AppTest harness: runs
app/main.py exactly as `streamlit run` would (sidebar navigation included)
and asserts every screen renders without raising, in the "no model
deployed" state (a real, expected state per SPEC_CONTRACT.md stage 2/3).

Isolated from any locally-deployed bundle/data via monkeypatched config
paths pointing at a tmp_path, so this test is reproducible regardless of
what (if anything) is currently deployed on the developer's machine.
"""
from __future__ import annotations

from pathlib import Path

import joblib
import pytest

# Resolve main.py absolutely. Streamlit changed how AppTest.from_file treats a
# relative path: older versions resolve it against the current working
# directory, newer ones against the file that calls from_file. A relative
# "app/main.py" therefore passes locally and fails on a machine with a newer
# Streamlit. An absolute path is correct on every version.
APP_MAIN = str(Path(__file__).resolve().parents[1] / "main.py")

from app import config, db

streamlit_testing = pytest.importorskip("streamlit.testing.v1")


@pytest.fixture(autouse=True)
def _isolated_paths(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "DB_PATH", tmp_path / "integration.db")
    monkeypatch.setattr(config, "MODEL_BUNDLE_PATH", tmp_path / "no_such_model_bundle.joblib")
    import app.model_service as model_service

    model_service.clear_cache()
    yield
    model_service.clear_cache()


def test_full_app_no_model_deployed_all_pages_render_without_exception():
    at = streamlit_testing.AppTest.from_file(APP_MAIN, default_timeout=30)
    at.run()
    assert not at.exception

    code_blocks = " ".join(e.value for e in at.code)
    assert "No classification model is deployed" in code_blocks

    for page in [
        "Battery Records",
        "Run Classification",
        "Maintenance Assessment",
        "Classification History",
        "Home",
    ]:
        at.sidebar.radio[0].set_value(page).run()
        assert not at.exception, f"page '{page}' raised: {at.exception}"


def test_classification_result_icon_is_not_duplicated(tmp_path, monkeypatch, small_bundle):
    """Regression test: the classification result alert must show the icon
    exactly once. A previous version passed the emoji in BOTH the message
    text and icon=, which rendered it twice side by side."""
    bundle_path = tmp_path / "model_bundle.joblib"
    joblib.dump(small_bundle, bundle_path)
    monkeypatch.setattr(config, "MODEL_BUNDLE_PATH", bundle_path)

    import app.model_service as model_service

    model_service.clear_cache()
    db.init_db()

    feature_names = [f["name"] for f in small_bundle["feature_spec"]["features"]]
    defaults = model_service.build_default_values(small_bundle)
    db.create_battery_record(
        "BAT-ICON-TEST", "EV-ICON-TEST", {k: defaults[k] for k in feature_names}
    )

    at = streamlit_testing.AppTest.from_file(APP_MAIN, default_timeout=30)
    at.run()
    at.sidebar.radio[0].set_value("Run Classification").run()
    assert not at.exception

    select_buttons = [b for b in at.button if b.label == "Select"]
    assert select_buttons, "expected at least one record to select"
    select_buttons[0].click().run()
    assert not at.exception

    classify_buttons = [b for b in at.button if "classify_form" in (b.key or "")]
    assert classify_buttons, "expected the Classify form submit button"
    classify_buttons[0].click().run()
    assert not at.exception, at.exception

    alerts = list(at.error) + list(at.success)
    result_alerts = [a for a in alerts if "FAILURE" in a.value]
    assert result_alerts, "expected a Failure/No Failure result alert"
    for alert in result_alerts:
        # The icon must come only from icon=, never duplicated into the
        # message text.
        assert "⚠" not in alert.value and "✅" not in alert.value, (
            f"result alert text still embeds an icon character: {alert.value!r}"
        )

    model_lines = [c.value for c in at.caption if c.value.startswith("Model: ")]
    assert model_lines, "expected a 'Model: ...' line on the result panel"
    assert "_" not in model_lines[0], f"algorithm name not formatted: {model_lines[0]!r}"
