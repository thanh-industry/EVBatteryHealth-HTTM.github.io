"""
Entry point: `streamlit run app/main.py`

Initializes the local SQLite database (FR-09) and routes between the five
screens that cover UC-06..UC-09 (plus the Home overview).
"""
from __future__ import annotations

import sys
from pathlib import Path

# Allow `from app import ...` to resolve when Streamlit sets sys.path[0] to
# this file's directory rather than the repo root.
_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

import streamlit as st  # noqa: E402

from app import config, db, model_service  # noqa: E402
from app.components.layout import render_sidebar  # noqa: E402
from app.pages_ import assessment, classify, history, home, records  # noqa: E402


def main() -> None:
    st.set_page_config(
        page_title=config.APP_TITLE,
        page_icon="\U0001F50B",
        layout="wide",
    )
    db.init_db()

    if "current_page" not in st.session_state:
        st.session_state["current_page"] = "Home"

    selected = render_sidebar(st.session_state["current_page"])
    st.session_state["current_page"] = selected

    if selected == "Home":
        home.render()
    elif selected == "Battery Records":
        records.render(model_service.get_status())
    elif selected == "Run Classification":
        classify.render(model_service.get_status())
    elif selected == "Maintenance Assessment":
        assessment.render()
    elif selected == "Classification History":
        history.render()


main()
