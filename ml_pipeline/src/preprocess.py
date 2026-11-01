"""Preprocessing pipeline builder.

Numeric features: median imputation + standard scaling.
Categorical features: most-frequent imputation + one-hot encoding (unknown
categories at inference time are ignored rather than raising, since the
deployed app must never crash on an unseen category).

Fit this only on the training partition (see src.pipeline.split_data) so
preprocessing statistics never leak information from the held-out test set.
"""
from __future__ import annotations

from typing import List

from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler


def build_preprocessor(numeric_cols: List[str], categorical_cols: List[str]) -> ColumnTransformer:
    """Build the ColumnTransformer used ahead of every estimator.

    Args:
        numeric_cols: names of numeric feature columns.
        categorical_cols: names of categorical feature columns.

    Returns:
        An unfitted ColumnTransformer: median-impute+scale for numeric
        columns, most-frequent-impute+one-hot for categorical columns.
    """
    numeric_pipeline = Pipeline(steps=[
        ("imputer", SimpleImputer(strategy="median")),
        ("scaler", StandardScaler()),
    ])
    categorical_pipeline = Pipeline(steps=[
        ("imputer", SimpleImputer(strategy="most_frequent")),
        ("encoder", OneHotEncoder(handle_unknown="ignore", sparse_output=False)),
    ])
    return ColumnTransformer(
        transformers=[
            ("num", numeric_pipeline, numeric_cols),
            ("cat", categorical_pipeline, categorical_cols),
        ]
    )
