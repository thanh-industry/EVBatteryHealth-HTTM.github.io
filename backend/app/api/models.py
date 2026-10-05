from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.security import require_role
from app.db.session import get_db
from app.models.dataset import Dataset
from app.models.model_deployment import ModelDeployment
from app.models.training_run import TrainingRun
from app.models.user import User
from app.schemas.models import ActiveModel
from app.schemas.training import TrainingRunOut
from app.services import training_service

router = APIRouter(prefix="/api/models", tags=["models"])

_require_data_scientist = require_role("data_scientist")


def _active_model_dict(db: Session, deployment: ModelDeployment) -> dict:
    run = db.get(TrainingRun, deployment.run_id)
    dataset = db.get(Dataset, run.dataset_id) if run else None
    run_dict = training_service.to_training_run_dict(db, run, dataset.name if dataset else "Unknown dataset")
    return {
        "run_id": run.id,
        "version": run_dict["version"],
        "algorithm": run.algorithm,
        "dataset_name": dataset.name if dataset else "Unknown dataset",
        "deployed_at": deployment.deployed_at,
        "metrics": run_dict["metrics"],
        "supports_probability": run.supports_probability,
    }


@router.get("", response_model=list[TrainingRunOut])
def list_models(
    db: Session = Depends(get_db), _user: User = Depends(_require_data_scientist)
) -> list[TrainingRunOut]:
    runs = (
        db.query(TrainingRun)
        .filter(TrainingRun.status == "completed")
        .order_by(TrainingRun.completed_at.desc())
        .all()
    )
    out = []
    for run in runs:
        dataset = db.get(Dataset, run.dataset_id)
        dataset_name = dataset.name if dataset else "Unknown dataset"
        out.append(TrainingRunOut(**training_service.to_training_run_dict(db, run, dataset_name)))
    return out


@router.get("/active", response_model=ActiveModel | None)
def get_active_model(
    db: Session = Depends(get_db), _user: User = Depends(_require_data_scientist)
) -> ActiveModel | None:
    deployment = db.query(ModelDeployment).filter(ModelDeployment.active.is_(True)).first()
    if deployment is None:
        return None
    return ActiveModel(**_active_model_dict(db, deployment))


@router.post("/{run_id}/deploy", response_model=ActiveModel)
def deploy_model(
    run_id: int, db: Session = Depends(get_db), _user: User = Depends(_require_data_scientist)
) -> ActiveModel:
    run = db.get(TrainingRun, run_id)
    if run is None:
        raise HTTPException(status_code=404, detail=f"Training run {run_id} not found.")
    if run.status != "completed":
        raise HTTPException(status_code=409, detail="Only a completed training run can be deployed.")

    db.query(ModelDeployment).filter(ModelDeployment.active.is_(True)).update({"active": False})
    deployment = ModelDeployment(run_id=run.id, deployed_at=datetime.now(timezone.utc), active=True)
    db.add(deployment)
    db.commit()
    db.refresh(deployment)

    return ActiveModel(**_active_model_dict(db, deployment))
