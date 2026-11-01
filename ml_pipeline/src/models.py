"""Model factory: Logistic Regression, SVM, Random Forest.

Each algorithm is built twice: once with default (uniform) class weights and
once with class_weight="balanced", giving the 6 configurations the spec (6.2,
6.3) requires us to train and compare.

SVC training cost is superlinear in the number of rows. To keep training time
bounded, SVM configurations are fit on a stratified subsample of the training
partition (SVM_TRAIN_ROW_CAP rows) rather than the full training set; this cap
is reported truthfully in the bundle metadata and printed by train.py.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Tuple

import pandas as pd
from sklearn.base import ClassifierMixin
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.svm import SVC

RANDOM_STATE = 42
SVM_TRAIN_ROW_CAP = 6000


@dataclass
class ModelConfig:
    """One of the 6 trainable configurations."""

    algorithm: str  # "logistic_regression" | "svm" | "random_forest"
    class_weight: Optional[str]  # None | "balanced"
    display_name: str
    estimator: ClassifierMixin


def build_model_configs() -> List[ModelConfig]:
    """Return the 6 configurations: {LR, SVM, RF} x {plain, balanced}."""
    configs: List[ModelConfig] = []

    for class_weight in (None, "balanced"):
        suffix = " (balanced)" if class_weight else ""
        configs.append(ModelConfig(
            algorithm="logistic_regression",
            class_weight=class_weight,
            display_name=f"Logistic Regression{suffix}",
            estimator=LogisticRegression(
                max_iter=1000, random_state=RANDOM_STATE, class_weight=class_weight,
            ),
        ))

    for class_weight in (None, "balanced"):
        suffix = " (balanced)" if class_weight else ""
        configs.append(ModelConfig(
            algorithm="svm",
            class_weight=class_weight,
            display_name=f"SVM{suffix}",
            estimator=SVC(
                kernel="rbf", C=1.0, gamma="scale",
                random_state=RANDOM_STATE, class_weight=class_weight,
            ),
        ))

    for class_weight in (None, "balanced"):
        suffix = " (balanced)" if class_weight else ""
        configs.append(ModelConfig(
            algorithm="random_forest",
            class_weight=class_weight,
            display_name=f"Random Forest{suffix}",
            estimator=RandomForestClassifier(
                n_estimators=100, random_state=RANDOM_STATE,
                class_weight=class_weight, n_jobs=-1,
            ),
        ))

    return configs


def subsample_stratified(
    X: pd.DataFrame, y: pd.Series, cap: int, random_state: int = RANDOM_STATE,
) -> Tuple[pd.DataFrame, pd.Series]:
    """Return a stratified subsample of at most `cap` rows, preserving class ratio.

    If len(X) <= cap, X and y are returned unchanged.
    """
    if len(X) <= cap:
        return X, y
    X_sub, _, y_sub, _ = train_test_split(
        X, y, train_size=cap, stratify=y, random_state=random_state,
    )
    return X_sub, y_sub
