"""Preprocessing must handle missing values: no NaN may reach the estimator."""
from __future__ import annotations

import numpy as np

from src import data as data_mod
from src.preprocess import build_preprocessor


def test_dataset_sample_has_real_missing_values(small_sample):
    """Sanity check: the test below is meaningful only if NaNs are present."""
    X, _ = data_mod.split_features_target(small_sample)
    assert X.isna().sum().sum() > 0


def test_preprocessor_output_has_no_nan(small_sample):
    X, _ = data_mod.split_features_target(small_sample)
    numeric_cols = data_mod.get_numeric_columns(small_sample)
    categorical_cols = data_mod.get_categorical_columns(small_sample)

    preprocessor = build_preprocessor(numeric_cols, categorical_cols)
    transformed = preprocessor.fit_transform(X)

    assert not np.isnan(transformed).any()


def test_preprocessor_imputes_median_and_most_frequent(small_sample):
    X, _ = data_mod.split_features_target(small_sample)
    numeric_cols = data_mod.get_numeric_columns(small_sample)
    categorical_cols = data_mod.get_categorical_columns(small_sample)

    preprocessor = build_preprocessor(numeric_cols, categorical_cols)
    preprocessor.fit(X)

    num_imputer = preprocessor.named_transformers_["num"].named_steps["imputer"]
    cat_imputer = preprocessor.named_transformers_["cat"].named_steps["imputer"]
    assert num_imputer.strategy == "median"
    assert cat_imputer.strategy == "most_frequent"
