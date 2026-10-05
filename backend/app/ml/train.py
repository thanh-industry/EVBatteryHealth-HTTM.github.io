"""Train/eval/persist one training run end to end.

Split-before-fit is mandatory: train_test_split happens on the full feature
frame FIRST, then the Pipeline (imputer/scaler/encoder/estimator) is fit on
the train partition only. Nothing is fit on the full frame before the split.
"""
import time
from dataclasses import dataclass

import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline

from app.core.config import settings
from app.ml import features, labeling
from app.ml.evaluate import compute_metrics, feature_importance_from_pipeline
from app.ml.pipeline import build_pipeline, supports_probability


@dataclass
class TrainResult:
    pipeline: Pipeline
    algorithm: str
    params: dict
    dropped_missing_label: int
    train_rows: int
    test_rows: int
    metrics: dict
    confusion_matrix: dict
    feature_importance: list[dict] | None
    supports_probability: bool
    duration_seconds: float
    numeric_columns: list[str]
    categorical_columns: list[str]


def _stratified_cap(X_train: pd.DataFrame, y_train: pd.Series, cap: int):
    """Deterministic stratified subsample of the TRAIN partition only (never
    the test partition), used to keep SVC training tractable on 20k rows.
    """
    if len(X_train) <= cap:
        return X_train, y_train
    X_capped, _X_rest, y_capped, _y_rest = train_test_split(
        X_train,
        y_train,
        train_size=cap,
        stratify=y_train,
        random_state=settings.RANDOM_STATE,
    )
    return X_capped, y_capped


def run_training(
    raw_df: pd.DataFrame,
    algorithm: str,
    params: dict,
    test_size: float,
) -> TrainResult:
    start = time.monotonic()

    labelled_df, dropped_missing_label = labeling.drop_missing_label(raw_df)
    y = labeling.labels_from_soh(labelled_df[settings.LABEL_SOURCE_COLUMN])
    X = features.build_feature_frame(labelled_df)
    features.assert_no_leakage(X)

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, stratify=y, random_state=settings.RANDOM_STATE
    )

    if algorithm == "svm":
        X_train, y_train = _stratified_cap(X_train, y_train, settings.SVM_MAX_TRAIN_ROWS)

    numeric_cols, categorical_cols = features.split_numeric_categorical(X_train)

    # Defense in depth: re-check the EXACT frame about to be fit (post-split,
    # post SVM subsampling), not just the pre-split frame above. This is the
    # guard that runs in production, not only in tests.
    features.assert_no_leakage(X_train)

    pipeline = build_pipeline(algorithm, params, numeric_cols, categorical_cols)
    pipeline.fit(X_train, y_train)

    y_pred = pipeline.predict(X_test)
    eval_result = compute_metrics(y_test, y_pred)
    feature_importance = feature_importance_from_pipeline(pipeline, algorithm)

    duration = time.monotonic() - start

    return TrainResult(
        pipeline=pipeline,
        algorithm=algorithm,
        params=params,
        dropped_missing_label=dropped_missing_label,
        train_rows=len(X_train),
        test_rows=len(X_test),
        metrics=eval_result["metrics"],
        confusion_matrix=eval_result["confusion_matrix"],
        feature_importance=feature_importance,
        supports_probability=supports_probability(algorithm),
        duration_seconds=duration,
        numeric_columns=numeric_cols,
        categorical_columns=categorical_cols,
    )
