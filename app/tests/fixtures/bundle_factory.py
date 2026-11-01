"""
Synthetic model_bundle.joblib builders used ONLY for tests and for local
integration smoke-testing of deployment/deploy_model.py and
deployment/verify_model.py while the real ml_pipeline bundle is not
yet available.

These bundles are structurally valid per SPEC_CONTRACT.md section 3 but are
NOT the graded machine-learning deliverable (that is ml_pipeline/, owned by
the offline pipeline). They exist so app/, deployment/ can be built and tested strictly
against the contract rather than waiting on the real artifact.

Two builders:
  - make_small_bundle(): a handful of features, fits in milliseconds, used
    by fast unit tests.
  - make_full_bundle_from_csv(): all 67 real feature columns sampled from
    the project dataset, used for end-to-end deploy/verify demonstrations.
"""
from __future__ import annotations

import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import sklearn
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    confusion_matrix,
    f1_score,
    precision_recall_fscore_support,
)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app import config  # noqa: E402


def _compute_metrics(
    y_true: np.ndarray, y_pred: np.ndarray, y_proba: np.ndarray | None
) -> dict[str, Any]:
    acc = accuracy_score(y_true, y_pred)
    precision, recall, f1, support = precision_recall_fscore_support(
        y_true, y_pred, labels=[0, 1], zero_division=0
    )
    cm = confusion_matrix(y_true, y_pred, labels=[0, 1]).tolist()
    macro_f1 = f1_score(y_true, y_pred, average="macro", zero_division=0)
    pr_auc = None
    if y_proba is not None:
        try:
            pr_auc = float(average_precision_score(y_true, y_proba))
        except Exception:  # noqa: BLE001
            pr_auc = None
    return {
        "accuracy": float(acc),
        "no_failure": {
            "precision": float(precision[0]),
            "recall": float(recall[0]),
            "f1": float(f1[0]),
            "support": int(support[0]),
        },
        "failure": {
            "precision": float(precision[1]),
            "recall": float(recall[1]),
            "f1": float(f1[1]),
            "support": int(support[1]),
        },
        "macro_f1": float(macro_f1),
        "pr_auc": pr_auc,
        "confusion_matrix": cm,
    }


def _build_feature_spec(
    X: pd.DataFrame,
    numeric_cols: list[str],
    categorical_cols: list[str],
    groups: dict[str, str],
    labels: dict[str, str],
    key_names: set[str],
) -> dict[str, Any]:
    features: list[dict[str, Any]] = []
    for name in numeric_cols:
        col = pd.to_numeric(X[name], errors="coerce")
        features.append(
            {
                "name": name,
                "kind": "numeric",
                "required": True,
                "min": float(col.min()),
                "max": float(col.max()),
                "median": float(col.median()),
                "allowed_values": None,
                "mode": None,
                "label": labels.get(name, name.replace("_", " ").title()),
                "group": groups.get(name, "other"),
                "key": name in key_names,
            }
        )
    for name in categorical_cols:
        col = X[name].astype("object")
        values = sorted(v for v in col.dropna().unique().tolist())
        mode_val = col.mode(dropna=True)
        features.append(
            {
                "name": name,
                "kind": "categorical",
                "required": True,
                "min": None,
                "max": None,
                "median": None,
                "allowed_values": [str(v) for v in values],
                "mode": str(mode_val.iloc[0]) if len(mode_val) else None,
                "label": labels.get(name, name.replace("_", " ").title()),
                "group": groups.get(name, "other"),
                "key": name in key_names,
            }
        )
    return {
        "version": "1.0",
        "features": features,
        "identifier_fields": list(config.IDENTIFIER_FIELDS),
    }


def _select_key_features(
    pipeline: Pipeline, numeric_cols: list[str], categorical_cols: list[str], top_n: int
) -> set[str]:
    """Rank original features by the fitted LogisticRegression's absolute
    standardized coefficient, aggregating one-hot dummy columns back to
    their source categorical feature by taking the max |coef| among them."""
    try:
        pre = pipeline.named_steps["pre"]
        clf = pipeline.named_steps["clf"]
        out_names = pre.get_feature_names_out()
        coefs = np.abs(clf.coef_[0])
    except Exception:  # noqa: BLE001
        # Fallback: no coefficients available (e.g. non-linear model) -
        # just take the first top_n numeric columns.
        return set(numeric_cols[:top_n])

    all_cols = numeric_cols + categorical_cols
    importance: dict[str, float] = {}
    for out_name, coef in zip(out_names, coefs):
        rest = out_name.split("__", 1)[1] if "__" in out_name else out_name
        best_match = None
        for orig in all_cols:
            if rest == orig or rest.startswith(orig + "_"):
                if best_match is None or len(orig) > len(best_match):
                    best_match = orig
        if best_match:
            importance[best_match] = max(importance.get(best_match, 0.0), float(coef))

    ranked = sorted(importance, key=lambda k: -importance[k])
    return set(ranked[:top_n])


def _fit_and_package(
    X: pd.DataFrame,
    y: pd.Series,
    numeric_cols: list[str],
    categorical_cols: list[str],
    groups: dict[str, str],
    labels: dict[str, str],
    random_state: int,
    top_n_key: int,
    algorithm: str = "logistic_regression",
    test_size: float = 0.25,
) -> dict[str, Any]:
    for col in categorical_cols:
        X[col] = X[col].astype("object")

    numeric_pipe = Pipeline(
        [("impute", SimpleImputer(strategy="median")), ("scale", StandardScaler())]
    )
    categorical_pipe = Pipeline(
        [
            ("impute", SimpleImputer(strategy="most_frequent")),
            ("onehot", OneHotEncoder(handle_unknown="ignore")),
        ]
    )
    pre = ColumnTransformer(
        [
            ("num", numeric_pipe, numeric_cols),
            ("cat", categorical_pipe, categorical_cols),
        ]
    )
    clf = LogisticRegression(max_iter=1000, class_weight="balanced")
    pipeline = Pipeline([("pre", pre), ("clf", clf)])

    stratify = y if y.nunique() > 1 else None
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=random_state, stratify=stratify
    )
    pipeline.fit(X_train, y_train)

    y_pred = pipeline.predict(X_test)
    y_proba = None
    supports_probability = hasattr(pipeline, "predict_proba")
    if supports_probability:
        classes = list(pipeline.classes_)
        idx1 = classes.index(1) if 1 in classes else len(classes) - 1
        y_proba = pipeline.predict_proba(X_test)[:, idx1]

    metrics = _compute_metrics(y_test.to_numpy(), y_pred, y_proba)
    key_names = _select_key_features(pipeline, numeric_cols, categorical_cols, top_n_key)
    feature_spec = _build_feature_spec(
        X, numeric_cols, categorical_cols, groups, labels, key_names
    )

    metadata = {
        "algorithm": algorithm,
        "class_weight": "balanced",
        "params": {k: v for k, v in clf.get_params().items()},
        "trained_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "sklearn_version": sklearn.__version__,
        "train_rows": int(len(X_train)),
        "test_rows": int(len(X_test)),
        "test_size": test_size,
        "random_state": random_state,
        "class_labels": {"0": "No Failure", "1": "Failure"},
        "decision_threshold": 0.5,
        "supports_probability": supports_probability,
        "metrics": metrics,
        "all_model_results": [dict(metrics, algorithm=algorithm)],
        "selection_rationale": (
            "SYNTHETIC TEST FIXTURE (not the real trained model): logistic "
            "regression chosen as a fast, interpretable baseline for "
            "integration-testing app/ and deployment/ against "
            "SPEC_CONTRACT.md section 3 ahead of the real ml_pipeline "
            "export. Key features were selected as the top absolute "
            "standardized coefficients from this fitted model."
        ),
    }

    return {"pipeline": pipeline, "feature_spec": feature_spec, "metadata": metadata}


def make_small_bundle(random_state: int = 42) -> dict[str, Any]:
    """A tiny 5-feature bundle (3 numeric, 2 categorical) for fast unit tests."""
    rng = np.random.RandomState(random_state)
    n = 400
    data = {
        "battery_health_percent": rng.uniform(40, 100, n),
        "cycle_count": rng.uniform(0, 3000, n),
        "internal_resistance": rng.uniform(0.1, 1.5, n),
        "battery_chemistry": rng.choice(["NMC", "LFP", "NCA"], n),
        "fleet_or_private": rng.choice(["Fleet", "Private"], n),
    }
    X = pd.DataFrame(data)
    risk = (100 - X["battery_health_percent"]) / 60 + X["internal_resistance"] / 1.5
    prob = 1 / (1 + np.exp(-(risk - 1.2) * 3))
    y = (rng.uniform(0, 1, n) < prob).astype(int)
    if y.sum() == 0:
        y[:5] = 1
    if y.sum() == n:
        y[:5] = 0

    numeric_cols = ["battery_health_percent", "cycle_count", "internal_resistance"]
    categorical_cols = ["battery_chemistry", "fleet_or_private"]
    groups = {
        "battery_health_percent": "battery_state",
        "cycle_count": "battery_state",
        "internal_resistance": "electrical",
        "battery_chemistry": "battery_spec",
        "fleet_or_private": "identity",
    }
    labels = {
        "battery_health_percent": "Battery Health (%)",
        "cycle_count": "Cycle Count",
        "internal_resistance": "Internal Resistance (ohm)",
        "battery_chemistry": "Battery Chemistry",
        "fleet_or_private": "Fleet or Private",
    }
    return _fit_and_package(
        X,
        pd.Series(y),
        numeric_cols,
        categorical_cols,
        groups,
        labels,
        random_state=random_state,
        top_n_key=2,
    )


# Explicit group assignment for the real 67 features, decided per
# SPEC_CONTRACT.md section 3.1 group vocabulary.
_REAL_FEATURE_GROUPS: dict[str, str] = {
    "vehicle_brand": "identity",
    "vehicle_model": "identity",
    "vehicle_type": "identity",
    "manufacturing_year": "identity",
    "drive_type": "identity",
    "odometer_km": "identity",
    "vehicle_age_years": "identity",
    "fleet_or_private": "identity",
    "battery_manufacturer": "battery_spec",
    "battery_chemistry": "battery_spec",
    "battery_capacity_kwh": "battery_spec",
    "cycle_count": "battery_state",
    "battery_health_percent": "battery_state",
    "state_of_charge": "battery_state",
    "depth_of_discharge": "battery_state",
    "state_of_health": "battery_state",
    "remaining_capacity": "battery_state",
    "capacity_loss_percent": "battery_state",
    "predicted_remaining_life_cycles": "battery_state",
    "cell_voltage_avg": "electrical",
    "cell_voltage_std": "electrical",
    "pack_voltage": "electrical",
    "cell_temperature_avg": "electrical",
    "cell_temperature_max": "electrical",
    "internal_resistance": "electrical",
    "voltage_imbalance": "electrical",
    "temperature_variance": "electrical",
    "sensor_fault_count": "electrical",
    "BMS_warning_count": "electrical",
    "abnormal_voltage_events": "electrical",
    "charge_efficiency": "charging",
    "discharge_efficiency": "charging",
    "charging_cycles_last_month": "charging",
    "fast_charge_ratio": "charging",
    "slow_charge_ratio": "charging",
    "average_charge_power_kw": "charging",
    "average_charging_time": "charging",
    "overnight_charging_ratio": "charging",
    "home_charging_ratio": "charging",
    "charging_interruptions": "charging",
    "overcharge_events": "charging",
    "charging_quality_score": "charging",
    "average_speed": "driving",
    "average_trip_distance": "driving",
    "aggressive_acceleration_score": "driving",
    "hard_braking_score": "driving",
    "regenerative_braking_usage": "driving",
    "highway_driving_ratio": "driving",
    "city_driving_ratio": "driving",
    "daily_distance": "driving",
    "driving_stress_score": "driving",
    "average_ambient_temperature": "environment",
    "maximum_temperature": "environment",
    "minimum_temperature": "environment",
    "humidity": "environment",
    "altitude": "environment",
    "terrain_type": "environment",
    "dust_exposure": "environment",
    "last_service_days": "maintenance",
    "cooling_system_health": "maintenance",
    "firmware_updates": "maintenance",
    "previous_faults": "maintenance",
    "maintenance_score": "maintenance",
    "thermal_runaway_risk": "risk",
    "battery_stress_index": "risk",
    "aging_score": "risk",
    "thermal_health_score": "risk",
}

_REAL_CATEGORICAL_COLS = list(config.CATEGORICAL_COLUMNS)


def make_full_bundle_from_csv(
    csv_path: Path | None = None,
    sample_rows: int = 4000,
    random_state: int = 42,
    algorithm: str = "logistic_regression",
) -> dict[str, Any]:
    """Build a bundle using all 67 real feature columns sampled from the
    project CSV, with a genuinely fitted LogisticRegression pipeline, real
    (if small-sample) metrics, and model-coefficient-driven key features."""
    csv_path = csv_path or config.RAW_DATASET_PATH
    all_cols = list(_REAL_FEATURE_GROUPS.keys()) + [config.TARGET_COLUMN]
    df = pd.read_csv(csv_path, usecols=all_cols)
    if sample_rows and sample_rows < len(df):
        df = df.sample(n=sample_rows, random_state=random_state).reset_index(drop=True)

    numeric_cols = [
        c
        for c in _REAL_FEATURE_GROUPS
        if c not in _REAL_CATEGORICAL_COLS
    ]
    categorical_cols = list(_REAL_CATEGORICAL_COLS)

    X = df[numeric_cols + categorical_cols].copy()
    y = df[config.TARGET_COLUMN].astype(int)

    labels = {c: c.replace("_", " ").replace("BMS", "BMS").title() for c in numeric_cols + categorical_cols}
    labels["BMS_warning_count"] = "BMS Warning Count"

    return _fit_and_package(
        X,
        y,
        numeric_cols,
        categorical_cols,
        _REAL_FEATURE_GROUPS,
        labels,
        random_state=random_state,
        top_n_key=12,
        algorithm=algorithm,
    )
