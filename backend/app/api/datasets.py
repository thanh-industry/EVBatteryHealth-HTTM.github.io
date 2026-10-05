from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile
from sqlalchemy.orm import Session

from app.core.security import require_role
from app.db.session import get_db
from app.models.dataset import Dataset
from app.models.user import User
from app.schemas.dataset import DataQuality, DatasetOut, DatasetPreview
from app.services import dataset_service

router = APIRouter(prefix="/api/datasets", tags=["datasets"])

_require_data_scientist = require_role("data_scientist")


def _get_dataset_or_404(db: Session, dataset_id: int) -> Dataset:
    dataset = db.get(Dataset, dataset_id)
    if dataset is None:
        raise HTTPException(status_code=404, detail=f"Dataset {dataset_id} not found.")
    return dataset


@router.get("", response_model=list[DatasetOut])
def list_datasets(
    db: Session = Depends(get_db), _user: User = Depends(_require_data_scientist)
) -> list[DatasetOut]:
    datasets = db.query(Dataset).order_by(Dataset.uploaded_at.desc()).all()
    return [DatasetOut.model_validate(d) for d in datasets]


@router.post("/upload", response_model=DatasetOut, status_code=201)
async def upload_dataset(
    file: UploadFile,
    db: Session = Depends(get_db),
    user: User = Depends(_require_data_scientist),
) -> DatasetOut:
    content = await file.read()
    df = dataset_service.parse_and_validate_csv(file.filename or "", content)
    dataset = dataset_service.create_dataset_record(
        db,
        name=file.filename or "dataset.csv",
        filename=file.filename or "dataset.csv",
        content=content,
        df=df,
        uploaded_by_user_id=user.id,
    )
    return DatasetOut.model_validate(dataset)


@router.get("/{dataset_id}", response_model=DatasetOut)
def get_dataset(
    dataset_id: int, db: Session = Depends(get_db), _user: User = Depends(_require_data_scientist)
) -> DatasetOut:
    dataset = _get_dataset_or_404(db, dataset_id)
    return DatasetOut.model_validate(dataset)


@router.get("/{dataset_id}/preview", response_model=DatasetPreview)
def preview_dataset(
    dataset_id: int,
    limit: int = Query(default=20, ge=1, le=500),
    db: Session = Depends(get_db),
    _user: User = Depends(_require_data_scientist),
) -> DatasetPreview:
    dataset = _get_dataset_or_404(db, dataset_id)
    df = dataset_service.load_dataset_dataframe(dataset)
    return DatasetPreview(**dataset_service.build_preview(df, limit))


@router.get("/{dataset_id}/quality", response_model=DataQuality)
def get_quality(
    dataset_id: int, db: Session = Depends(get_db), _user: User = Depends(_require_data_scientist)
) -> DataQuality:
    dataset = _get_dataset_or_404(db, dataset_id)
    df = dataset_service.load_dataset_dataframe(dataset)
    quality = dataset_service.build_data_quality(dataset_id, df)
    return DataQuality(**quality)


@router.delete("/{dataset_id}", status_code=204)
def delete_dataset(
    dataset_id: int, db: Session = Depends(get_db), _user: User = Depends(_require_data_scientist)
) -> None:
    dataset = _get_dataset_or_404(db, dataset_id)
    db.delete(dataset)
    db.commit()
    return None
