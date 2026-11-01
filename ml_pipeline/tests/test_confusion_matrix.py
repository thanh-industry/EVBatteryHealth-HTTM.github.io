"""The confusion matrix must be 2x2 and its row sums must equal class supports."""
from __future__ import annotations

import numpy as np

from src.evaluate import compute_metrics, trivial_baseline_metrics


def test_confusion_matrix_shape_and_row_sums():
    y_true = [0] * 90 + [1] * 10
    y_pred = [0] * 85 + [1] * 5 + [0] * 3 + [1] * 7  # 90 then 10 predictions

    metrics = compute_metrics(y_true, y_pred)
    cm = np.array(metrics["confusion_matrix"])

    assert cm.shape == (2, 2)
    assert cm[0].sum() == metrics["no_failure"]["support"]
    assert cm[1].sum() == metrics["failure"]["support"]
    assert int(cm.sum()) == len(y_true)
    assert metrics["no_failure"]["support"] + metrics["failure"]["support"] == len(y_true)


def test_trivial_baseline_matches_accuracy_trap():
    y_true = [0] * 93 + [1] * 7
    metrics = trivial_baseline_metrics(y_true)
    cm = np.array(metrics["confusion_matrix"])

    assert cm.shape == (2, 2)
    assert metrics["failure"]["recall"] == 0.0
    assert metrics["failure"]["support"] == 7
    assert metrics["no_failure"]["support"] == 93
    assert np.isclose(metrics["accuracy"], 0.93)
