"""Training run orchestration: create -> run in threadpool -> persist status
and results. Status always progresses pending -> running -> completed/failed.
"""
import json
from datetime import datetime, timezone

from fastapi.concurrency import run_in_threadpool
from sqlalchemy.orm import Session

from app.core.config import settings
from app.ml import registry
from app.ml.train import run_training
from app.models.dataset import Dataset
from app.models.model_deployment import ModelDeployment
from app.models.training_run import TrainingRun


def merge_params(algorithm: str, provided: dict | None) -> dict:
    merged = dict(settings.DEFAULT_PARAMS[algorithm])
    if provided:
        merged.update(provided)
    return merged


def create_pending_run(
    db: Session, dataset_id: int, algorithm: str, test_size: float, params: dict, user_id: int | None
) -> TrainingRun:
    run = TrainingRun(
        dataset_id=dataset_id,
        algorithm=algorithm,
        params_json=json.dumps(params),
        test_size=test_size,
        status="pending",
        started_at=datetime.now(timezone.utc),
        supports_probability=False,
        created_by_user_id=user_id,
    )
    db.add(run)
    db.commit()
    db.refresh(run)
    return run


async def execute_training(db: Session, run: TrainingRun, dataset: Dataset) -> TrainingRun:
    run.status = "running"
    db.commit()

    from app.services.dataset_service import load_dataset_dataframe

    try:
        df = load_dataset_dataframe(dataset)
        params = json.loads(run.params_json)
        result = await run_in_threadpool(run_training, df, run.algorithm, params, run.test_size)
    except Exception as exc:
        run.status = "failed"
        run.error = str(exc)
        run.completed_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(run)
        return run

    model_path = registry.save_model(run.id, result.pipeline)

    run.status = "completed"
    run.error = None
    run.completed_at = datetime.now(timezone.utc)
    run.duration_seconds = result.duration_seconds
    run.dropped_missing_label = result.dropped_missing_label
    run.train_rows = result.train_rows
    run.test_rows = result.test_rows
    run.metrics_json = json.dumps(result.metrics)
    run.confusion_matrix_json = json.dumps(result.confusion_matrix)
    run.feature_importance_json = (
        json.dumps(result.feature_importance) if result.feature_importance is not None else None
    )
    run.supports_probability = result.supports_probability
    run.model_path = model_path
    db.commit()
    db.refresh(run)
    return run


def version_for_run(run: TrainingRun) -> str | None:
    if run.status != "completed":
        return None
    return f"v{run.id}"


def is_run_deployed(db: Session, run_id: int) -> bool:
    active = (
        db.query(ModelDeployment)
        .filter(ModelDeployment.run_id == run_id, ModelDeployment.active.is_(True))
        .first()
    )
    return active is not None


def to_training_run_dict(db: Session, run: TrainingRun, dataset_name: str) -> dict:
    return {
        "id": run.id,
        "dataset_id": run.dataset_id,
        "dataset_name": dataset_name,
        "algorithm": run.algorithm,
        "params": json.loads(run.params_json) if run.params_json else {},
        "test_size": run.test_size,
        "status": run.status,
        "error": run.error,
        "started_at": run.started_at,
        "completed_at": run.completed_at,
        "duration_seconds": run.duration_seconds,
        "train_rows": run.train_rows,
        "test_rows": run.test_rows,
        "metrics": json.loads(run.metrics_json) if run.metrics_json else None,
        "confusion_matrix": json.loads(run.confusion_matrix_json) if run.confusion_matrix_json else None,
        "feature_importance": (
            json.loads(run.feature_importance_json) if run.feature_importance_json else None
        ),
        "supports_probability": run.supports_probability,
        "is_deployed": is_run_deployed(db, run.id),
        "version": version_for_run(run),
    }
