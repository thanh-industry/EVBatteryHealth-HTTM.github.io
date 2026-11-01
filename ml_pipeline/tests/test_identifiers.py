"""Identifier columns must never enter the feature matrix."""
from __future__ import annotations

from src import data as data_mod


def test_identifier_columns_excluded_from_features(small_sample):
    X, y = data_mod.split_features_target(small_sample)

    assert "vehicle_id" not in X.columns
    assert "battery_serial" not in X.columns
    assert "battery_failure" not in X.columns
    assert len(X.columns) == 67


def test_identifier_columns_excluded_from_numeric_and_categorical_lists(small_sample):
    numeric_cols = data_mod.get_numeric_columns(small_sample)
    categorical_cols = data_mod.get_categorical_columns(small_sample)

    assert "vehicle_id" not in numeric_cols
    assert "vehicle_id" not in categorical_cols
    assert "battery_serial" not in numeric_cols
    assert "battery_serial" not in categorical_cols
    assert len(numeric_cols) == 59
    assert len(categorical_cols) == 8
    assert len(numeric_cols) + len(categorical_cols) == 67
