from __future__ import annotations

from pathlib import Path

import joblib
import pytest

from app import model_service


def test_get_status_missing_file_is_clean_not_raising(tmp_path):
    missing = tmp_path / "does_not_exist.joblib"
    status = model_service.get_status(path=missing, force_reload=True)
    assert status.deployed is False
    assert status.bundle is None
    assert status.error is not None
    assert "deploy" in status.error.lower() or "no model" in status.error.lower()


def test_get_status_corrupt_file_is_clean_not_raising(tmp_path):
    corrupt = tmp_path / "corrupt.joblib"
    corrupt.write_bytes(b"this is not a valid joblib pickle")
    status = model_service.get_status(path=corrupt, force_reload=True)
    assert status.deployed is False
    assert status.bundle is None
    assert status.error is not None


def test_get_status_invalid_structure_is_clean_not_raising(tmp_path):
    bad = tmp_path / "bad_structure.joblib"
    joblib.dump({"pipeline": None}, bad)  # missing feature_spec/metadata
    status = model_service.get_status(path=bad, force_reload=True)
    assert status.deployed is False
    assert "missing" in status.error.lower() or "predict" in status.error.lower()


def test_get_status_valid_bundle_deploys_cleanly(tmp_path, small_bundle):
    path = tmp_path / "model_bundle.joblib"
    joblib.dump(small_bundle, path)
    status = model_service.get_status(path=path, force_reload=True)
    assert status.deployed is True
    assert status.bundle is not None
    assert status.error is None


def test_validate_input_accepts_valid_defaults(small_bundle):
    values = model_service.build_default_values(small_bundle)
    ok, errors = model_service.validate_input(values, small_bundle["feature_spec"])
    assert ok is True
    assert errors == []


def test_validate_input_rejects_missing_required(small_bundle):
    values = model_service.build_default_values(small_bundle)
    required_feature = next(
        f for f in small_bundle["feature_spec"]["features"] if f.get("required", True)
    )
    del values[required_feature["name"]]
    ok, errors = model_service.validate_input(values, small_bundle["feature_spec"])
    assert ok is False
    assert any(required_feature["name"] in e or required_feature["label"] in e for e in errors)


def test_validate_input_rejects_out_of_range_numeric(small_bundle):
    values = model_service.build_default_values(small_bundle)
    numeric_feature = next(
        f for f in small_bundle["feature_spec"]["features"] if f["kind"] == "numeric"
    )
    values[numeric_feature["name"]] = numeric_feature["max"] + 1_000_000
    ok, errors = model_service.validate_input(values, small_bundle["feature_spec"])
    assert ok is False
    assert len(errors) >= 1


def test_validate_input_rejects_unknown_category(small_bundle):
    values = model_service.build_default_values(small_bundle)
    cat_feature = next(
        f for f in small_bundle["feature_spec"]["features"] if f["kind"] == "categorical"
    )
    values[cat_feature["name"]] = "__NOT_A_REAL_CATEGORY__"
    ok, errors = model_service.validate_input(values, small_bundle["feature_spec"])
    assert ok is False


def test_predict_returns_valid_label(small_bundle):
    values = model_service.build_default_values(small_bundle)
    result = model_service.predict(small_bundle, values)
    assert result.prediction in (0, 1)
    assert result.label in ("No Failure", "Failure")
    if small_bundle["metadata"]["supports_probability"]:
        assert result.probability is not None
        assert 0.0 <= result.probability <= 1.0


def test_predict_carries_model_provenance(small_bundle):
    """Each prediction must carry the algorithm/trained_at that produced
    it, independent of whatever bundle happens to be deployed later - this
    is what lets the result panel and history show which model produced a
    given result (FR-14)."""
    values = model_service.build_default_values(small_bundle)
    result = model_service.predict(small_bundle, values)
    assert result.model_algorithm == small_bundle["metadata"]["algorithm"]
    assert result.model_trained_at == str(small_bundle["metadata"]["trained_at"])
