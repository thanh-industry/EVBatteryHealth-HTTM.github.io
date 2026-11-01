"""feature_spec must cover exactly the 67 expected features."""
from __future__ import annotations

from pathlib import Path

import joblib
import pytest

from src.data import CATEGORICAL_COLS, FEATURE_GROUP_ORDER, ID_COLS, TARGET_COL

ARTIFACTS_DIR = Path(__file__).resolve().parents[1] / "artifacts"
EXPECTED_FEATURE_COUNT = 67
EXPECTED_NUMERIC_COUNT = 59
EXPECTED_CATEGORICAL_COUNT = 8


@pytest.fixture(scope="module")
def feature_spec():
    bundle_path = ARTIFACTS_DIR / "model_bundle.joblib"
    if not bundle_path.exists():
        pytest.skip(f"{bundle_path} not found; run train.py first")
    bundle = joblib.load(bundle_path)
    return bundle["feature_spec"]


def test_feature_spec_has_exactly_67_unique_features(feature_spec):
    names = [f["name"] for f in feature_spec["features"]]
    assert len(names) == EXPECTED_FEATURE_COUNT
    assert len(set(names)) == EXPECTED_FEATURE_COUNT


def test_feature_spec_excludes_identifiers_and_target(feature_spec):
    names = {f["name"] for f in feature_spec["features"]}
    for id_col in ID_COLS:
        assert id_col not in names
    assert TARGET_COL not in names
    assert feature_spec["identifier_fields"] == ID_COLS


def test_feature_spec_numeric_categorical_split(feature_spec):
    numeric = [f for f in feature_spec["features"] if f["kind"] == "numeric"]
    categorical = [f for f in feature_spec["features"] if f["kind"] == "categorical"]
    assert len(numeric) == EXPECTED_NUMERIC_COUNT
    assert len(categorical) == EXPECTED_CATEGORICAL_COUNT
    assert {f["name"] for f in categorical} == set(CATEGORICAL_COLS)


def test_feature_spec_entries_well_formed(feature_spec):
    for f in feature_spec["features"]:
        assert f["label"]
        assert f["group"] in FEATURE_GROUP_ORDER
        if f["kind"] == "numeric":
            assert f["min"] is not None and f["max"] is not None and f["median"] is not None
            assert f["min"] <= f["median"] <= f["max"]
            assert f["allowed_values"] is None
        else:
            assert f["allowed_values"] is not None and len(f["allowed_values"]) > 0
            assert f["mode"] in f["allowed_values"]


def test_feature_spec_marks_about_12_key_features(feature_spec):
    key_names = [f["name"] for f in feature_spec["features"] if f.get("key")]
    assert 10 <= len(key_names) <= 14
