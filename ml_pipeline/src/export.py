"""Model bundle export: feature_spec + metadata + the fitted pipeline.

Produces exactly the structure defined in SPEC_CONTRACT.md section 3 - the
interface another agent's Streamlit app builds against.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Set

import joblib
import numpy as np
import pandas as pd
import sklearn
from sklearn.pipeline import Pipeline

from .data import CLASS_LABELS, FEATURE_GROUPS, ID_COLS, feature_label

KEY_FEATURE_COUNT = 12


def _expanded_name_to_original(expanded_name: str, categorical_cols: List[str]) -> str:
    """Map a ColumnTransformer expanded feature name back to its original column.

    Expanded names look like "num__cycle_count" or
    "cat__vehicle_brand_Ford" (OneHotEncoder's default "{col}_{category}"
    combiner under a ColumnTransformer with verbose_feature_names_out=True).
    """
    if expanded_name.startswith("num__"):
        return expanded_name[len("num__"):]
    if expanded_name.startswith("cat__"):
        rest = expanded_name[len("cat__"):]
        for col in categorical_cols:
            if rest == col or rest.startswith(col + "_"):
                return col
        return rest
    return expanded_name


def compute_key_features(
    pipeline: Pipeline,
    numeric_cols: List[str],
    categorical_cols: List[str],
    top_n: int = KEY_FEATURE_COUNT,
) -> List[str]:
    """Return the top_n original feature names most predictive of failure.

    Method depends on the fitted estimator inside the pipeline:
      - Logistic Regression: abs(coefficient) per original feature.
      - Random Forest: feature_importances_ per original feature.
    A categorical column expands into one one-hot column per level; its
    original-feature importance is the MAX (not sum) of its levels'
    importances. Sum was tried first and rejected: it mechanically favors
    high-cardinality columns (e.g. vehicle_model has 42 levels, so summing
    42 small coefficients outranks genuinely predictive numeric risk
    features even though no single level is influential). Max represents
    "the single strongest effect this feature can have" and is comparable
    across numeric and categorical features on equal footing.

    Any other estimator falls back to feature_importances_ if present, else
    coef_.
    """
    preprocessor = pipeline.named_steps["preprocessor"]
    estimator = pipeline.named_steps["estimator"]
    expanded_names = preprocessor.get_feature_names_out()

    if hasattr(estimator, "coef_"):
        raw_importance = np.abs(estimator.coef_).ravel()
    elif hasattr(estimator, "feature_importances_"):
        raw_importance = np.asarray(estimator.feature_importances_).ravel()
    else:
        raise ValueError(
            f"Estimator {type(estimator).__name__} exposes neither coef_ nor "
            "feature_importances_; cannot derive key features."
        )

    agg: Dict[str, float] = {}
    for name, importance in zip(expanded_names, raw_importance):
        original = _expanded_name_to_original(name, categorical_cols)
        agg[original] = max(agg.get(original, 0.0), float(importance))

    ranked = sorted(agg.items(), key=lambda kv: kv[1], reverse=True)
    return [name for name, _ in ranked[:top_n]]


def key_feature_method_description(algorithm: str) -> str:
    if algorithm == "logistic_regression":
        return (
            "abs(coefficient) of the fitted Logistic Regression model on the "
            "standardized/encoded features; a categorical feature's one-hot "
            "levels are aggregated by taking the MAX absolute coefficient "
            "across its levels (not the sum, which would mechanically favor "
            "high-cardinality columns such as vehicle_model), then the top "
            "12 original features by that value are marked key."
        )
    if algorithm == "random_forest":
        return (
            "feature_importances_ (mean decrease in impurity) of the fitted "
            "Random Forest; a categorical feature's one-hot levels are "
            "aggregated by taking the MAX importance across its levels (not "
            "the sum, which would mechanically favor high-cardinality "
            "columns), then the top 12 original features by that value are "
            "marked key."
        )
    return (
        f"max aggregate feature importance derived from the fitted {algorithm} "
        "estimator across each feature's encoded columns; the top 12 "
        "original features by that value are marked key."
    )


def build_feature_spec(
    X_train: pd.DataFrame,
    numeric_cols: List[str],
    categorical_cols: List[str],
    key_features: Set[str],
) -> Dict:
    """Build the feature_spec dict (SPEC_CONTRACT.md section 3) from the
    training partition only (min/max/median/allowed_values/mode must reflect
    training data, not the held-out test set).
    """
    features = []
    for col in X_train.columns:
        if col in numeric_cols:
            series = X_train[col].astype(float)
            entry = {
                "name": col,
                "kind": "numeric",
                "required": True,
                "min": float(series.min()),
                "max": float(series.max()),
                "median": float(series.median()),
                "allowed_values": None,
                "mode": None,
                "label": feature_label(col),
                "group": FEATURE_GROUPS[col],
            }
        elif col in categorical_cols:
            series = X_train[col]
            mode_series = series.mode(dropna=True)
            mode_val = str(mode_series.iloc[0]) if len(mode_series) else None
            allowed = sorted(str(v) for v in series.dropna().unique().tolist())
            entry = {
                "name": col,
                "kind": "categorical",
                "required": True,
                "min": None,
                "max": None,
                "median": None,
                "allowed_values": allowed,
                "mode": mode_val,
                "label": feature_label(col),
                "group": FEATURE_GROUPS[col],
            }
        else:
            raise ValueError(f"Column {col} is neither numeric nor categorical")

        if col in key_features:
            entry["key"] = True
        features.append(entry)

    return {
        "version": "1.0",
        "features": features,
        "identifier_fields": list(ID_COLS),
    }


def build_metadata(
    algorithm: str,
    class_weight,
    params: Dict,
    train_rows: int,
    test_rows: int,
    test_size: float,
    random_state: int,
    decision_threshold: float,
    supports_probability: bool,
    metrics: Dict,
    all_model_results: List[Dict],
    selection_rationale: str,
    key_feature_method: str,
) -> Dict:
    """Build the metadata dict (SPEC_CONTRACT.md section 3)."""
    safe_params = {k: v for k, v in params.items() if _is_json_safe(v)}
    return {
        "algorithm": algorithm,
        "class_weight": class_weight,
        "params": safe_params,
        "trained_at": datetime.now(timezone.utc).isoformat(),
        "sklearn_version": sklearn.__version__,
        "train_rows": int(train_rows),
        "test_rows": int(test_rows),
        "test_size": float(test_size),
        "random_state": int(random_state),
        "class_labels": {str(k): v for k, v in CLASS_LABELS.items()},
        "decision_threshold": float(decision_threshold),
        "supports_probability": bool(supports_probability),
        "metrics": metrics,
        "all_model_results": all_model_results,
        "selection_rationale": selection_rationale,
        "key_feature_method": key_feature_method,
    }


def _is_json_safe(value) -> bool:
    try:
        json.dumps(value)
        return True
    except TypeError:
        return False


def build_bundle(pipeline: Pipeline, feature_spec: Dict, metadata: Dict) -> Dict:
    """Assemble the final bundle dict ready for joblib.dump."""
    return {"pipeline": pipeline, "feature_spec": feature_spec, "metadata": metadata}


def save_bundle(bundle: Dict, out_path: str) -> None:
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(bundle, out_path)


def save_json(obj: Dict, out_path: str) -> None:
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="ascii", errors="backslashreplace") as f:
        json.dump(obj, f, indent=2)
