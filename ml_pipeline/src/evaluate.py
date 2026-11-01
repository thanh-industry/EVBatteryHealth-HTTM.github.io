"""Evaluation metrics: accuracy, per-class precision/recall/f1, confusion
matrix, PR-AUC, cross-validation, and the trivial all-zero baseline.

Per spec FR-04 / 6.3, metrics are reported per class with the minority
Failure class (label 1) foregrounded, never accuracy alone.
"""
from __future__ import annotations

from typing import Dict, Optional

import numpy as np
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    confusion_matrix,
    f1_score,
    precision_recall_fscore_support,
)
from sklearn.model_selection import StratifiedKFold, cross_val_score

NO_FAILURE = 0
FAILURE = 1


def compute_metrics(y_true, y_pred, y_score: Optional[np.ndarray] = None) -> Dict:
    """Compute the metrics dict matching SPEC_CONTRACT.md section 3 "metrics" shape.

    Args:
        y_true: ground-truth labels (0/1).
        y_pred: predicted labels (0/1).
        y_score: optional continuous score (probability or decision function)
            for the positive (Failure) class, used for PR-AUC. None if the
            estimator cannot produce one (e.g. SVC without probability=True
            and no decision_function available).

    Returns:
        dict with accuracy, per-class {precision, recall, f1, support} for
        "no_failure" and "failure", macro_f1, pr_auc (float or None), and
        confusion_matrix as [[TN, FP], [FN, TP]].
    """
    accuracy = float(accuracy_score(y_true, y_pred))
    precision, recall, f1, support = precision_recall_fscore_support(
        y_true, y_pred, labels=[NO_FAILURE, FAILURE], zero_division=0,
    )
    cm = confusion_matrix(y_true, y_pred, labels=[NO_FAILURE, FAILURE])
    macro_f1 = float(f1_score(y_true, y_pred, average="macro", zero_division=0))

    pr_auc = None
    if y_score is not None:
        pr_auc = float(average_precision_score(y_true, y_score))

    return {
        "accuracy": accuracy,
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
        "macro_f1": macro_f1,
        "pr_auc": pr_auc,
        "confusion_matrix": cm.tolist(),
    }


def trivial_baseline_metrics(y_true) -> Dict:
    """Metrics for a trivial classifier that always predicts "No Failure".

    Demonstrates the accuracy trap: high accuracy, zero Failure-class recall.
    """
    y_true_arr = np.asarray(y_true)
    y_pred_zero = np.zeros_like(y_true_arr)
    return compute_metrics(y_true_arr, y_pred_zero, y_score=None)


def cross_validate_f1_failure(estimator, X, y, cv: int = 5, random_state: int = 42) -> Dict:
    """Stratified k-fold cross-validation, scoring F1 on the Failure class.

    The estimator is cloned fresh for each fold by scikit-learn internally;
    passing an already-fitted estimator/pipeline is safe.
    """
    skf = StratifiedKFold(n_splits=cv, shuffle=True, random_state=random_state)
    scores = cross_val_score(estimator, X, y, cv=skf, scoring="f1")
    return {
        "cv_folds": cv,
        "f1_failure_mean": float(scores.mean()),
        "f1_failure_std": float(scores.std()),
        "f1_failure_per_fold": [float(s) for s in scores],
    }
