import joblib
import pytest
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline

from app.ml.registry import ModelLoadError, load_model, model_path_for_run, save_model


def test_save_and_load_roundtrip(tmp_storage_dirs):
    pipeline = Pipeline(steps=[("estimator", LogisticRegression())])
    path = save_model(999, pipeline)
    loaded = load_model(path)
    assert isinstance(loaded, Pipeline)


def test_load_missing_artifact_raises_clean_error(tmp_storage_dirs):
    path = model_path_for_run(123456)
    with pytest.raises(ModelLoadError):
        load_model(str(path))


def test_load_corrupt_artifact_raises_clean_error(tmp_storage_dirs):
    path = model_path_for_run(42)
    path.write_bytes(b"not a valid joblib pickle file")
    with pytest.raises(ModelLoadError):
        load_model(str(path))


def test_load_non_pipeline_artifact_raises_clean_error(tmp_storage_dirs):
    path = model_path_for_run(43)
    joblib.dump({"not": "a pipeline"}, path)
    with pytest.raises(ModelLoadError):
        load_model(str(path))
