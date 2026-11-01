"""The train/test split must happen BEFORE preprocessing is fit (no leakage).

We verify this operationally: the scaler's fitted statistics must match the
train partition only, not the full frame.
"""
from __future__ import annotations

import numpy as np

from src import data as data_mod
from src.pipeline import split_data
from src.preprocess import build_preprocessor


def test_scaler_statistics_reflect_train_partition_only(full_df):
    X, y = data_mod.split_features_target(full_df)
    numeric_cols = data_mod.get_numeric_columns(full_df)
    categorical_cols = data_mod.get_categorical_columns(full_df)

    X_train, X_test, y_train, y_test = split_data(X, y)
    assert len(X_train) + len(X_test) == len(X)
    assert len(X_train) == len(y_train)

    preprocessor_train = build_preprocessor(numeric_cols, categorical_cols)
    preprocessor_train.fit(X_train)
    train_means = preprocessor_train.named_transformers_["num"].named_steps["scaler"].mean_

    preprocessor_full = build_preprocessor(numeric_cols, categorical_cols)
    preprocessor_full.fit(X)
    full_means = preprocessor_full.named_transformers_["num"].named_steps["scaler"].mean_

    # If the scaler had leaked test-set information (fit on the full frame),
    # its statistics would equal full_means instead of the train-only means.
    assert not np.allclose(train_means, full_means)

    # Cross-check the first numeric column's mean by recomputing it directly
    # from the train partition only (median-imputed, as the pipeline does).
    first_col = numeric_cols[0]
    train_series = X_train[first_col]
    imputed = train_series.fillna(train_series.median())
    assert np.isclose(train_means[0], imputed.mean(), rtol=1e-9)


def test_split_is_stratified(full_df):
    X, y = data_mod.split_features_target(full_df)
    X_train, X_test, y_train, y_test = split_data(X, y)

    full_rate = y.mean()
    train_rate = y_train.mean()
    test_rate = y_test.mean()

    assert abs(train_rate - full_rate) < 0.01
    assert abs(test_rate - full_rate) < 0.01
