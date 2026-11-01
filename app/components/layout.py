"""Sidebar navigation and footer shared by every page."""
from __future__ import annotations

import streamlit as st

from app import config, db, model_service
from app.components.status import render_model_badge

PAGES = [
    "Home",
    "Battery Records",
    "Run Classification",
    "Maintenance Assessment",
    "Classification History",
]


def render_sidebar(current_page: str) -> str:
    """Renders the sidebar navigation + status + footer. Returns the
    selected page name."""
    with st.sidebar:
        st.markdown(f"### {config.APP_TITLE}")
        selected = st.radio(
            "Navigate",
            PAGES,
            index=PAGES.index(current_page) if current_page in PAGES else 0,
            label_visibility="collapsed",
        )

        st.divider()
        status = model_service.get_status()
        render_model_badge(status)

        st.divider()
        render_footer()

    return selected


def render_footer() -> None:
    info = config.COURSE_INFO
    st.caption(info["university_line1"])
    st.caption(info["university_line2"])
    st.caption(info["faculty"])
    st.caption(f"Course: {info['course']}")
    st.caption(f"Instructor: {info['instructor']}")
    st.markdown(f"**{info['group']}**")
    for student in info["students"]:
        st.caption(student)
