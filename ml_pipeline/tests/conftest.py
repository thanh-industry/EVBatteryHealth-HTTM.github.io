"""Shared pytest fixtures for the ml_pipeline test suite.

Inserts ml_pipeline/ onto sys.path so tests can `from src import ...`
regardless of the directory pytest is invoked from, and provides a small,
class-stratified sample of the real dataset so tests run fast.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import pytest

ML_PIPELINE_DIR = Path(__file__).resolve().parents[1]
if str(ML_PIPELINE_DIR) not in sys.path:
    sys.path.insert(0, str(ML_PIPELINE_DIR))

from src import data as data_mod  # noqa: E402

CSV_PATH = ML_PIPELINE_DIR.parent / "ev battery_failure prediction Dataset.csv"
ARTIFACTS_DIR = ML_PIPELINE_DIR / "artifacts"


@pytest.fixture(scope="session")
def full_df() -> pd.DataFrame:
    return data_mod.load_dataset(str(CSV_PATH))


@pytest.fixture(scope="session")
def small_sample(full_df: pd.DataFrame) -> pd.DataFrame:
    """A small, class-stratified sample (300 rows) of the real dataset.

    Keeps both classes well represented (60 Failure / 240 No Failure) so
    stratified splits and small cross-validation folds remain valid, while
    keeping tests fast.
    """
    pos = full_df[full_df["battery_failure"] == 1].sample(n=60, random_state=42)
    neg = full_df[full_df["battery_failure"] == 0].sample(n=240, random_state=42)
    sample = pd.concat([pos, neg]).sample(frac=1.0, random_state=42).reset_index(drop=True)
    return sample
