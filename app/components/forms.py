"""
Battery parameter input form (used by Battery Records and Run Classification).

Usability decision from SPEC_CONTRACT.md section 3.1: 67 inputs is too many
to type, so the ~12 features marked "key": true in the bundle are shown in an
always-visible section; the rest sit inside collapsed per-group expanders,
pre-filled with median/mode defaults. The model always receives all 67
values - this module's job is only to collect them with a UI that does not
feel like a 67-field wall.
"""
from __future__ import annotations

from typing import Any

import streamlit as st

from app import config, model_service


def _step_for(min_v: float | None, max_v: float | None) -> float:
    if min_v is None or max_v is None:
        return 0.1
    span = max_v - min_v
    if span <= 0:
        return 0.1
    if span < 5:
        return 0.01
    if span < 100:
        return 0.1
    return 1.0


def _clamped(value: float, min_v: float | None, max_v: float | None) -> float:
    if min_v is not None and value < min_v:
        value = float(min_v)
    if max_v is not None and value > max_v:
        value = float(max_v)
    return value


def _render_single_field(
    feat: dict[str, Any],
    defaults: dict[str, Any],
    current_values: dict[str, Any],
    key_prefix: str,
) -> Any:
    name = feat["name"]
    widget_key = f"{key_prefix}__{name}"
    current = current_values.get(name, defaults.get(name))

    if feat["kind"] == "numeric":
        min_v = feat.get("min")
        max_v = feat.get("max")
        try:
            val = float(current) if current is not None else float(feat.get("median") or 0.0)
        except (TypeError, ValueError):
            val = float(feat.get("median") or 0.0)
        val = _clamped(val, min_v, max_v)
        kwargs: dict[str, Any] = {"step": _step_for(min_v, max_v)}
        if min_v is not None:
            kwargs["min_value"] = float(min_v)
        if max_v is not None:
            kwargs["max_value"] = float(max_v)
        help_text = f"{name}"
        if min_v is not None and max_v is not None:
            help_text += f"  (valid range: {min_v:g} to {max_v:g})"
        return st.number_input(
            feat["label"], value=val, key=widget_key, help=help_text, **kwargs
        )

    # categorical
    options = feat.get("allowed_values") or []
    if not options:
        return st.text_input(
            feat["label"], value=str(current or ""), key=widget_key, help=name
        )
    if current not in options:
        current = feat.get("mode") if feat.get("mode") in options else options[0]
    index = options.index(current)
    return st.selectbox(
        feat["label"], options=options, index=index, key=widget_key, help=name
    )


def _render_feature_grid(
    feats: list[dict[str, Any]],
    defaults: dict[str, Any],
    current_values: dict[str, Any],
    key_prefix: str,
    n_cols: int = 3,
) -> dict[str, Any]:
    values: dict[str, Any] = {}
    cols = st.columns(n_cols)
    for i, feat in enumerate(feats):
        with cols[i % n_cols]:
            values[feat["name"]] = _render_single_field(
                feat, defaults, current_values, key_prefix
            )
    return values


def render_feature_form(
    bundle: dict[str, Any],
    current_values: dict[str, Any] | None = None,
    key_prefix: str = "form",
) -> dict[str, Any]:
    """Render the full 67-feature input form (key features always visible,
    the rest in collapsed per-group expanders) and return the collected
    values as a dict of {feature_name: value}."""
    features = model_service.get_features(bundle)
    defaults = model_service.build_default_values(bundle)
    current_values = current_values or {}

    values: dict[str, Any] = {}

    keys = model_service.key_features(features)
    others = model_service.non_key_features(features)

    if keys:
        st.markdown("##### Key parameters")
        st.caption(
            f"The {len(keys)} features most predictive of failure. "
            "Review and adjust these first."
        )
        values.update(_render_feature_grid(keys, defaults, current_values, f"{key_prefix}_key"))

    st.markdown("##### Additional parameters")
    st.caption(
        "Pre-filled with the training dataset's median/mode. Expand a group "
        "to review or edit; otherwise the defaults are used as-is."
    )
    grouped = model_service.group_features(others)
    for group, feats in grouped.items():
        label = config.FEATURE_GROUP_LABELS.get(group, group.replace("_", " ").title())
        with st.expander(f"{label} ({len(feats)} fields)", expanded=False):
            values.update(
                _render_feature_grid(feats, defaults, current_values, f"{key_prefix}_{group}")
            )

    return values
