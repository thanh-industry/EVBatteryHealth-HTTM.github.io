"""All 3 algorithms must train on a small sample and return metrics in [0, 1]."""
from __future__ import annotations

from src import data as data_mod
from src.models import build_model_configs
from src.pipeline import fit_and_evaluate_one, split_data


def test_all_algorithms_train_and_produce_valid_metrics(small_sample):
    X, y = data_mod.split_features_target(small_sample)
    numeric_cols = data_mod.get_numeric_columns(small_sample)
    categorical_cols = data_mod.get_categorical_columns(small_sample)
    X_train, X_test, y_train, y_test = split_data(X, y, test_size=0.3, random_state=42)

    configs = build_model_configs()
    algos_seen = set()

    for cfg in configs:
        result = fit_and_evaluate_one(
            cfg, X_train, y_train, X_test, y_test, numeric_cols, categorical_cols, cv_folds=2,
        )
        algos_seen.add(cfg.algorithm)

        m = result.metrics
        assert 0.0 <= m["accuracy"] <= 1.0
        for cls in ("no_failure", "failure"):
            assert 0.0 <= m[cls]["precision"] <= 1.0
            assert 0.0 <= m[cls]["recall"] <= 1.0
            assert 0.0 <= m[cls]["f1"] <= 1.0
            assert m[cls]["support"] >= 0
        assert 0.0 <= m["macro_f1"] <= 1.0
        if m["pr_auc"] is not None:
            assert 0.0 <= m["pr_auc"] <= 1.0
        assert 0.0 <= result.cv["f1_failure_mean"] <= 1.0
        assert result.fit_seconds >= 0.0

    assert algos_seen == {"logistic_regression", "svm", "random_forest"}
    assert len(configs) == 6  # 3 algorithms x {plain, balanced}
