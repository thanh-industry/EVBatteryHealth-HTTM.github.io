"""joblib persistence for trained pipelines. Handles a missing or corrupt
artifact file without ever surfacing a stack trace to the caller.
"""
from pathlib import Path

import joblib
from sklearn.pipeline import Pipeline

from app.core.config import settings


class ModelLoadError(Exception):
    """Raised when a model artifact is missing, corrupt, or unreadable."""


def model_path_for_run(run_id: int) -> Path:
    return settings.MODELS_DIR / f"run_{run_id}.joblib"


def save_model(run_id: int, pipeline: Pipeline) -> str:
    path = model_path_for_run(run_id)
    joblib.dump(pipeline, path)
    return str(path)


def load_model(model_path: str) -> Pipeline:
    path = Path(model_path)
    if not path.exists():
        raise ModelLoadError(f"Model artifact not found: {path.name}")
    try:
        pipeline = joblib.load(path)
    except Exception as exc:  # corrupt pickle, truncated file, version mismatch, etc.
        raise ModelLoadError(f"Model artifact is corrupt or unreadable: {path.name}") from exc
    if not isinstance(pipeline, Pipeline):
        raise ModelLoadError(f"Model artifact is not a valid pipeline: {path.name}")
    return pipeline
