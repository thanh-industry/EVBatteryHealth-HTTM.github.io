"""The exported bundle must round-trip: load it, predict on sample rows, get
valid output. Requires ml_pipeline/artifacts/model_bundle.joblib to exist
(run train.py first; see ml_pipeline/README.md).
"""
from __future__ import annotations

from pathlib import Path

import joblib
import pytest

ARTIFACTS_DIR = Path(__file__).resolve().parents[1] / "artifacts"


@pytest.fixture(scope="module")
def bundle():
    bundle_path = ARTIFACTS_DIR / "model_bundle.joblib"
    if not bundle_path.exists():
        pytest.skip(f"{bundle_path} not found; run train.py first")
    return joblib.load(bundle_path)


def test_bundle_has_required_top_level_keys(bundle):
    assert set(bundle.keys()) == {"pipeline", "feature_spec", "metadata"}


def test_bundle_predicts_on_sample_rows(bundle, small_sample):
    pipeline = bundle["pipeline"]
    feature_names = [f["name"] for f in bundle["feature_spec"]["features"]]

    sample_rows = small_sample[feature_names].head(5)
    preds = pipeline.predict(sample_rows)

    assert len(preds) == 5
    assert set(preds.tolist()).issubset({0, 1})


def test_bundle_probability_output_is_valid_when_supported(bundle, small_sample):
    pipeline = bundle["pipeline"]
    feature_names = [f["name"] for f in bundle["feature_spec"]["features"]]
    sample_rows = small_sample[feature_names].head(5)

    if bundle["metadata"]["supports_probability"]:
        assert hasattr(pipeline, "predict_proba")
        proba = pipeline.predict_proba(sample_rows)
        assert proba.shape == (5, 2)
        assert ((proba >= 0.0) & (proba <= 1.0)).all()
        row_sums = proba.sum(axis=1)
        assert (abs(row_sums - 1.0) < 1e-6).all()
    else:
        assert bundle["metadata"]["supports_probability"] is False
