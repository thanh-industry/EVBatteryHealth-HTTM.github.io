"""
Model loading, input validation, and inference (FR-06, FR-07, FR-08).

This module is Streamlit-agnostic on purpose: it can be imported and unit
tested with plain pytest, and is also used by deployment/verify_model.py.

A missing or corrupt bundle is never allowed to raise out of get_status():
callers always get a BundleStatus with deployed=False and a human-readable
reason instead of a stack trace.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

import joblib
import pandas as pd

from app import config
from deployment.deploy_model import validate_bundle


@dataclass
class BundleStatus:
    deployed: bool
    bundle: Optional[dict[str, Any]]
    error: Optional[str]
    path: Path


@dataclass
class PredictionResult:
    prediction: int
    label: str
    probability: Optional[float]
    model_algorithm: str
    model_trained_at: str


# mtime-keyed cache so repeated Streamlit reruns don't reload the bundle
# from disk unless the deployed file actually changed.
_cache: dict[str, tuple[Optional[float], BundleStatus]] = {}


def _load(path: Path) -> BundleStatus:
    if not path.exists():
        return BundleStatus(
            deployed=False,
            bundle=None,
            error=(
                "No model is deployed yet. The Software Developer must run "
                "'python deployment/deploy_model.py' to deploy a trained "
                "model before classification is available."
            ),
            path=path,
        )
    try:
        bundle = joblib.load(path)
    except Exception as exc:  # noqa: BLE001 - must never crash the UI
        return BundleStatus(
            deployed=False,
            bundle=None,
            error=f"Deployed model file is corrupt or unreadable: {exc}",
            path=path,
        )
    if not isinstance(bundle, dict):
        return BundleStatus(
            deployed=False,
            bundle=None,
            error="Deployed model file is not a valid bundle (expected a dict).",
            path=path,
        )
    problems = validate_bundle(bundle)
    if problems:
        return BundleStatus(
            deployed=False,
            bundle=None,
            error="Deployed model bundle failed validation: " + "; ".join(problems),
            path=path,
        )
    return BundleStatus(deployed=True, bundle=bundle, error=None, path=path)


def get_status(
    path: Optional[Path] = None, force_reload: bool = False
) -> BundleStatus:
    """Return the current deployed-model status, loading (and caching) it
    from disk as needed. Never raises."""
    resolved = Path(path) if path is not None else config.MODEL_BUNDLE_PATH
    key = str(resolved)
    try:
        mtime = resolved.stat().st_mtime if resolved.exists() else None
    except OSError:
        mtime = None
    if not force_reload and key in _cache and _cache[key][0] == mtime:
        return _cache[key][1]
    status = _load(resolved)
    _cache[key] = (mtime, status)
    return status


def clear_cache() -> None:
    _cache.clear()


# --------------------------------------------------------------------- #
# Feature spec helpers
# --------------------------------------------------------------------- #

def get_features(bundle: dict[str, Any]) -> list[dict[str, Any]]:
    return bundle["feature_spec"]["features"]


def default_value_for(feature: dict[str, Any]) -> Any:
    if feature["kind"] == "numeric":
        return feature.get("median")
    return feature.get("mode")


def build_default_values(bundle: dict[str, Any]) -> dict[str, Any]:
    """All 67 features pre-filled with their median/mode default."""
    return {f["name"]: default_value_for(f) for f in get_features(bundle)}


def group_features(
    features: list[dict[str, Any]],
) -> dict[str, list[dict[str, Any]]]:
    """Group features by their UI group, preserving SPEC_CONTRACT group order
    for known groups and appending any unexpected group names at the end."""
    grouped: dict[str, list[dict[str, Any]]] = {g: [] for g in config.FEATURE_GROUP_ORDER}
    for feat in features:
        grouped.setdefault(feat.get("group", "other"), []).append(feat)
    # drop empty known groups, keep insertion order for extras
    ordered: dict[str, list[dict[str, Any]]] = {}
    for g in config.FEATURE_GROUP_ORDER:
        if grouped.get(g):
            ordered[g] = grouped[g]
    for g, feats in grouped.items():
        if g not in config.FEATURE_GROUP_ORDER and feats:
            ordered[g] = feats
    return ordered


def key_features(features: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [f for f in features if f.get("key")]


def non_key_features(features: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [f for f in features if not f.get("key")]


# --------------------------------------------------------------------- #
# Validation (FR-07)
# --------------------------------------------------------------------- #

def validate_input(
    values: dict[str, Any], feature_spec: dict[str, Any]
) -> tuple[bool, list[str]]:
    """Validate a dict of feature values against the bundle's feature_spec.

    Checks: every required feature present, numeric values parse and fall
    within [min, max] when given, categorical values are in allowed_values.
    Returns (is_valid, list_of_error_messages).
    """
    errors: list[str] = []
    for feat in feature_spec["features"]:
        name = feat["name"]
        label = feat.get("label", name)
        required = feat.get("required", True)
        kind = feat["kind"]
        value = values.get(name)
        is_missing = value is None or (isinstance(value, str) and value.strip() == "")

        if is_missing:
            if required:
                errors.append(f"'{label}' is required but missing.")
            continue

        if kind == "numeric":
            try:
                numeric_value = float(value)
            except (TypeError, ValueError):
                errors.append(f"'{label}' must be a number (got {value!r}).")
                continue
            min_v = feat.get("min")
            max_v = feat.get("max")
            if min_v is not None and numeric_value < min_v:
                errors.append(
                    f"'{label}' must be >= {min_v} (got {numeric_value})."
                )
            if max_v is not None and numeric_value > max_v:
                errors.append(
                    f"'{label}' must be <= {max_v} (got {numeric_value})."
                )
        elif kind == "categorical":
            allowed = feat.get("allowed_values") or []
            if allowed and value not in allowed:
                errors.append(
                    f"'{label}' must be one of {allowed} (got {value!r})."
                )
        else:
            errors.append(f"'{label}' has an unsupported kind '{kind}'.")

    return (len(errors) == 0, errors)


# --------------------------------------------------------------------- #
# Inference (FR-08)
# --------------------------------------------------------------------- #

def _build_row(
    values: dict[str, Any], features: list[dict[str, Any]]
) -> pd.DataFrame:
    row: dict[str, Any] = {}
    for feat in features:
        name = feat["name"]
        value = values.get(name, default_value_for(feat))
        if feat["kind"] == "numeric" and value is not None and value != "":
            value = float(value)
        row[name] = value
    columns = [f["name"] for f in features]
    return pd.DataFrame([row], columns=columns)


def predict(bundle: dict[str, Any], values: dict[str, Any]) -> PredictionResult:
    """Run inference for a single record. Caller is responsible for having
    validated `values` first (FR-07 happens before FR-08)."""
    pipeline = bundle["pipeline"]
    metadata = bundle["metadata"]
    features = get_features(bundle)

    df = _build_row(values, features)
    raw_prediction = pipeline.predict(df)[0]
    prediction = int(raw_prediction)

    class_labels = metadata.get("class_labels") or {}
    label = class_labels.get(str(prediction)) or config.CLASS_LABELS.get(
        prediction, str(prediction)
    )

    probability: Optional[float] = None
    supports_probability = bool(metadata.get("supports_probability"))
    if supports_probability and hasattr(pipeline, "predict_proba"):
        try:
            proba_row = pipeline.predict_proba(df)[0]
            classes = list(getattr(pipeline, "classes_", [0, 1]))
            failure_idx = classes.index(1) if 1 in classes else len(proba_row) - 1
            probability = float(proba_row[failure_idx])
        except Exception:  # noqa: BLE001 - probability is best-effort only
            probability = None

    return PredictionResult(
        prediction=prediction,
        label=label,
        probability=probability,
        model_algorithm=str(metadata.get("algorithm", "unknown")),
        model_trained_at=str(metadata.get("trained_at", "unknown")),
    )
