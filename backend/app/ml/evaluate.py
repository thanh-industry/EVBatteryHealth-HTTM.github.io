"""Metric computation on held-out predictions. Real numbers only, from the
test set the caller passes in - never fabricated or hard-coded.
"""
import numpy as np
from sklearn.metrics import accuracy_score, confusion_matrix, precision_recall_fscore_support

from app.core.config import settings


def compute_metrics(y_true, y_pred) -> dict:
    labels = settings.SOH_CLASSES
    accuracy = float(accuracy_score(y_true, y_pred))

    precision_macro, recall_macro, f1_macro, _ = precision_recall_fscore_support(
        y_true, y_pred, labels=labels, average="macro", zero_division=0
    )
    precision_per, recall_per, f1_per, support_per = precision_recall_fscore_support(
        y_true, y_pred, labels=labels, average=None, zero_division=0
    )

    per_class = [
        {
            "class": labels[i],
            "precision": float(precision_per[i]),
            "recall": float(recall_per[i]),
            "f1": float(f1_per[i]),
            "support": int(support_per[i]),
        }
        for i in range(len(labels))
    ]

    metrics = {
        "accuracy": accuracy,
        "precision_macro": float(precision_macro),
        "recall_macro": float(recall_macro),
        "f1_macro": float(f1_macro),
        "per_class": per_class,
    }

    cm = confusion_matrix(y_true, y_pred, labels=labels)
    confusion = {"labels": labels, "matrix": cm.tolist()}

    return {"metrics": metrics, "confusion_matrix": confusion}


def feature_importance_from_pipeline(pipeline, algorithm: str) -> list[dict] | None:
    """RF/LogReg only (ARCHITECTURE.md 4.4). Null for SVM regardless of kernel -
    coefficients after one-hot encoding are not a meaningful importance for SVC.
    """
    if algorithm not in ("random_forest", "logistic_regression"):
        return None

    preprocessor = pipeline.named_steps["preprocess"]
    estimator = pipeline.named_steps["estimator"]
    feature_names = list(preprocessor.get_feature_names_out())

    if algorithm == "random_forest":
        importances = estimator.feature_importances_
    else:
        # LogisticRegression.coef_ has shape (n_classes, n_features) for
        # multiclass. Average the absolute coefficient across classes.
        importances = np.mean(np.abs(estimator.coef_), axis=0)

    pairs = sorted(zip(feature_names, importances), key=lambda p: p[1], reverse=True)
    return [{"feature": name, "importance": float(value)} for name, value in pairs]
