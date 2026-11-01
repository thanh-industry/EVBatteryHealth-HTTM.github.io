"""Orchestration: split -> train -> evaluate -> select.

This module is imported by both the notebook and train.py so the training
logic exists exactly once (see ml_pipeline/README.md). The notebook calls
`fit_and_evaluate_one` inside a visible loop for narrative purposes; train.py
calls `run_all_experiments` directly for brevity.
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional

import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline

from .evaluate import compute_metrics, cross_validate_f1_failure
from .models import (
    RANDOM_STATE,
    SVM_TRAIN_ROW_CAP,
    ModelConfig,
    build_model_configs,
    subsample_stratified,
)
from .preprocess import build_preprocessor

TEST_SIZE = 0.2


@dataclass
class TrainedResult:
    """Everything produced by training and evaluating one configuration."""

    algorithm: str
    class_weight: Optional[str]
    display_name: str
    pipeline: Pipeline
    metrics: Dict
    cv: Dict
    train_rows: int
    test_rows: int
    fit_seconds: float
    svm_row_cap_applied: bool
    params: Dict = field(default_factory=dict)


def split_data(X: pd.DataFrame, y: pd.Series, test_size: float = TEST_SIZE, random_state: int = RANDOM_STATE):
    """Stratified 80/20 train/test split, done BEFORE any preprocessing is fit.

    Splitting first (rather than scaling/imputing on the full frame and
    splitting afterwards) prevents leakage: the imputer's median/mode and the
    scaler's mean/std are fit on the training partition only, so no
    information about the held-out test rows ever reaches the model.
    """
    return train_test_split(X, y, test_size=test_size, stratify=y, random_state=random_state)


def fit_and_evaluate_one(
    cfg: ModelConfig,
    X_train: pd.DataFrame,
    y_train: pd.Series,
    X_test: pd.DataFrame,
    y_test: pd.Series,
    numeric_cols: List[str],
    categorical_cols: List[str],
    cv_folds: int = 5,
    svm_row_cap: int = SVM_TRAIN_ROW_CAP,
) -> TrainedResult:
    """Fit one model configuration, evaluate on the held-out test set, and
    cross-validate on the (possibly capped) training partition.
    """
    preprocessor = build_preprocessor(numeric_cols, categorical_cols)
    pipe = Pipeline(steps=[("preprocessor", preprocessor), ("estimator", cfg.estimator)])

    fit_X, fit_y = X_train, y_train
    svm_row_cap_applied = False
    if cfg.algorithm == "svm" and len(X_train) > svm_row_cap:
        fit_X, fit_y = subsample_stratified(X_train, y_train, svm_row_cap, RANDOM_STATE)
        svm_row_cap_applied = True

    t0 = time.perf_counter()
    pipe.fit(fit_X, fit_y)
    fit_seconds = time.perf_counter() - t0

    y_pred = pipe.predict(X_test)
    if hasattr(pipe, "predict_proba"):
        y_score = pipe.predict_proba(X_test)[:, 1]
    elif hasattr(pipe, "decision_function"):
        y_score = pipe.decision_function(X_test)
    else:
        y_score = None
    metrics = compute_metrics(y_test, y_pred, y_score)

    # Cross-validate on the same (possibly capped) partition used for fitting,
    # so SVM cross-validation cost stays bounded too.
    cv = cross_validate_f1_failure(pipe, fit_X, fit_y, cv=cv_folds, random_state=RANDOM_STATE)

    return TrainedResult(
        algorithm=cfg.algorithm,
        class_weight=cfg.class_weight,
        display_name=cfg.display_name,
        pipeline=pipe,
        metrics=metrics,
        cv=cv,
        train_rows=len(fit_X),
        test_rows=len(X_test),
        fit_seconds=fit_seconds,
        svm_row_cap_applied=svm_row_cap_applied,
        params={k: v for k, v in cfg.estimator.get_params().items()},
    )


def run_all_experiments(
    X_train: pd.DataFrame,
    y_train: pd.Series,
    X_test: pd.DataFrame,
    y_test: pd.Series,
    numeric_cols: List[str],
    categorical_cols: List[str],
    cv_folds: int = 5,
) -> List[TrainedResult]:
    """Train and evaluate all 6 configurations. Returns one TrainedResult each."""
    results = []
    for cfg in build_model_configs():
        results.append(
            fit_and_evaluate_one(
                cfg, X_train, y_train, X_test, y_test, numeric_cols, categorical_cols, cv_folds,
            )
        )
    return results


def select_best_result(results: List[TrainedResult]) -> TrainedResult:
    """Pick the configuration with the highest F1-score on the Failure class.

    Per spec 6.3, selection must be driven by Precision/Recall/F1 on the
    Failure class, never accuracy.
    """
    return max(results, key=lambda r: r.metrics["failure"]["f1"])


def results_as_table(results: List[TrainedResult]) -> pd.DataFrame:
    """A comparison DataFrame: one row per configuration, Failure-class first."""
    rows = []
    for r in results:
        rows.append({
            "model": r.display_name,
            "algorithm": r.algorithm,
            "class_weight": r.class_weight or "none",
            "accuracy": r.metrics["accuracy"],
            "precision_failure": r.metrics["failure"]["precision"],
            "recall_failure": r.metrics["failure"]["recall"],
            "f1_failure": r.metrics["failure"]["f1"],
            "precision_no_failure": r.metrics["no_failure"]["precision"],
            "recall_no_failure": r.metrics["no_failure"]["recall"],
            "f1_no_failure": r.metrics["no_failure"]["f1"],
            "macro_f1": r.metrics["macro_f1"],
            "pr_auc": r.metrics["pr_auc"],
            "cv_f1_failure_mean": r.cv["f1_failure_mean"],
            "cv_f1_failure_std": r.cv["f1_failure_std"],
            "fit_seconds": r.fit_seconds,
            "train_rows": r.train_rows,
            "svm_row_cap_applied": r.svm_row_cap_applied,
        })
    return pd.DataFrame(rows)
