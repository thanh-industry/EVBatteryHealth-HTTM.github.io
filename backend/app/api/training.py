from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.security import require_role
from app.db.session import get_db
from app.models.dataset import Dataset
from app.models.training_run import TrainingRun
from app.models.user import User
from app.schemas.training import TrainingRequest, TrainingRunOut
from app.services import training_service

router = APIRouter(prefix="/api/training", tags=["training"])

_require_data_scientist = require_role("data_scientist")


@router.post("/runs", response_model=TrainingRunOut, status_code=201)
async def create_training_run(
    body: TrainingRequest,
    db: Session = Depends(get_db),
    user: User = Depends(_require_data_scientist),
) -> TrainingRunOut:
    dataset = db.get(Dataset, body.dataset_id)
    if dataset is None:
        raise HTTPException(status_code=404, detail=f"Dataset {body.dataset_id} not found.")

    params = training_service.merge_params(body.algorithm, body.params)
    run = training_service.create_pending_run(
        db, dataset.id, body.algorithm, body.test_size, params, user.id
    )
    run = await training_service.execute_training(db, run, dataset)
    return TrainingRunOut(**training_service.to_training_run_dict(db, run, dataset.name))


@router.get("/runs", response_model=list[TrainingRunOut])
def list_training_runs(
    db: Session = Depends(get_db), _user: User = Depends(_require_data_scientist)
) -> list[TrainingRunOut]:
    runs = db.query(TrainingRun).order_by(TrainingRun.started_at.desc()).all()
    out = []
    for run in runs:
        dataset = db.get(Dataset, run.dataset_id)
        dataset_name = dataset.name if dataset else "Unknown dataset"
        out.append(TrainingRunOut(**training_service.to_training_run_dict(db, run, dataset_name)))
    return out


@router.get("/runs/{run_id}", response_model=TrainingRunOut)
def get_training_run(
    run_id: int, db: Session = Depends(get_db), _user: User = Depends(_require_data_scientist)
) -> TrainingRunOut:
    run = db.get(TrainingRun, run_id)
    if run is None:
        raise HTTPException(status_code=404, detail=f"Training run {run_id} not found.")
    dataset = db.get(Dataset, run.dataset_id)
    dataset_name = dataset.name if dataset else "Unknown dataset"
    return TrainingRunOut(**training_service.to_training_run_dict(db, run, dataset_name))
