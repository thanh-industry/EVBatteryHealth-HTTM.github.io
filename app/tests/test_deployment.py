from __future__ import annotations

import copy

import joblib
import pytest

from deployment import deploy_model, verify_model


# --------------------------------------------------------------------- #
# deploy_model.validate_bundle
# --------------------------------------------------------------------- #

def test_validate_bundle_accepts_valid_bundle(small_bundle):
    problems = deploy_model.validate_bundle(small_bundle)
    assert problems == []


def test_validate_bundle_rejects_missing_top_level_key(small_bundle):
    bad = copy.deepcopy(small_bundle)
    del bad["metadata"]
    problems = deploy_model.validate_bundle(bad)
    assert any("metadata" in p for p in problems)


def test_validate_bundle_rejects_pipeline_without_predict(small_bundle):
    bad = dict(small_bundle)
    bad["pipeline"] = object()
    problems = deploy_model.validate_bundle(bad)
    assert any("predict" in p for p in problems)


def test_validate_bundle_rejects_feature_missing_keys(small_bundle):
    bad = copy.deepcopy(small_bundle)
    del bad["feature_spec"]["features"][0]["label"]
    problems = deploy_model.validate_bundle(bad)
    assert any("missing keys" in p for p in problems)


def test_validate_bundle_rejects_empty_features(small_bundle):
    bad = copy.deepcopy(small_bundle)
    bad["feature_spec"]["features"] = []
    problems = deploy_model.validate_bundle(bad)
    assert any("non-empty" in p for p in problems)


def test_validate_bundle_rejects_missing_failure_metrics(small_bundle):
    bad = copy.deepcopy(small_bundle)
    del bad["metadata"]["metrics"]["failure"]["recall"]
    problems = deploy_model.validate_bundle(bad)
    assert any("failure" in p for p in problems)


# --------------------------------------------------------------------- #
# deploy_model.deploy / main
# --------------------------------------------------------------------- #

def test_deploy_copies_valid_bundle(tmp_path, small_bundle):
    src = tmp_path / "source_bundle.joblib"
    joblib.dump(small_bundle, src)
    target_dir = tmp_path / "models"

    deployed_path = deploy_model.deploy(src, target_dir)

    assert deployed_path == target_dir / "model_bundle.joblib"
    assert deployed_path.exists()
    reloaded = joblib.load(deployed_path)
    assert set(reloaded.keys()) == {"pipeline", "feature_spec", "metadata"}


def test_deploy_raises_on_invalid_bundle_and_does_not_deploy(tmp_path):
    src = tmp_path / "bad_bundle.joblib"
    joblib.dump({"pipeline": object()}, src)
    target_dir = tmp_path / "models"

    with pytest.raises(deploy_model.ValidationError):
        deploy_model.deploy(src, target_dir)
    assert not (target_dir / "model_bundle.joblib").exists()


def test_main_exits_nonzero_and_does_not_deploy_on_missing_file(tmp_path, capsys):
    missing = tmp_path / "nope.joblib"
    target_dir = tmp_path / "models"
    code = deploy_model.main(["--bundle", str(missing), "--target", str(target_dir)])
    assert code == 1
    assert not (target_dir / "model_bundle.joblib").exists()


def test_main_deploys_and_exits_zero_on_valid_bundle(tmp_path, small_bundle, capsys):
    src = tmp_path / "source_bundle.joblib"
    joblib.dump(small_bundle, src)
    target_dir = tmp_path / "models"

    code = deploy_model.main(["--bundle", str(src), "--target", str(target_dir)])

    assert code == 0
    assert (target_dir / "model_bundle.joblib").exists()
    out = capsys.readouterr().out
    assert "DEPLOYMENT SUCCESSFUL" in out
    assert small_bundle["metadata"]["algorithm"] in out


# --------------------------------------------------------------------- #
# verify_model
# --------------------------------------------------------------------- #

def test_verify_model_all_checks_pass_against_deployed_small_bundle(tmp_path, small_bundle, capsys):
    deployed_path = tmp_path / "model_bundle.joblib"
    joblib.dump(small_bundle, deployed_path)

    code = verify_model.main(["--bundle", str(deployed_path), "--sample-size", "30"])

    out = capsys.readouterr().out
    assert code == 0
    assert "0 failed" in out


def test_verify_model_reports_failure_when_bundle_missing(tmp_path, capsys):
    missing = tmp_path / "model_bundle.joblib"
    code = verify_model.main(["--bundle", str(missing)])
    out = capsys.readouterr().out
    assert code == 1
    assert "FAIL" in out
