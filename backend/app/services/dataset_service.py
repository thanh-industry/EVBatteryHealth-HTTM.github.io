"""Dataset upload validation, persistence, preview and data-quality reporting."""
import io
from datetime import datetime, timezone

import numpy as np
import pandas as pd
from fastapi import HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.core.config import settings
from app.ml import features, labeling
from app.models.dataset import Dataset


def _reject(detail: str) -> None:
    raise HTTPException(status_code=400, detail=detail)


def parse_and_validate_csv(filename: str, content: bytes) -> pd.DataFrame:
    """Validate an uploaded CSV per ARCHITECTURE.md 4.3. Raises 400 with a
    clear detail message on any failure.
    """
    if not filename.lower().endswith(settings.ALLOWED_UPLOAD_EXTENSION):
        _reject("Only .csv files are accepted.")

    if len(content) == 0:
        _reject("Uploaded file is empty.")

    max_bytes = settings.MAX_UPLOAD_MB * 1024 * 1024
    if len(content) > max_bytes:
        _reject(f"File exceeds the maximum allowed size of {settings.MAX_UPLOAD_MB} MB.")

    try:
        df = pd.read_csv(io.BytesIO(content))
    except Exception:
        _reject("Unable to parse file as CSV.")

    if df.shape[0] == 0 or df.shape[1] == 0:
        _reject("Uploaded CSV file contains no data.")

    if settings.LABEL_SOURCE_COLUMN not in df.columns:
        _reject(f"CSV file must contain a '{settings.LABEL_SOURCE_COLUMN}' column.")

    return df


def compute_basic_stats(df: pd.DataFrame) -> dict:
    row_count, column_count = df.shape
    missing_cells = int(df.isna().sum().sum())
    total_cells = row_count * column_count
    missing_pct = float(missing_cells / total_cells * 100) if total_cells else 0.0
    duplicate_rows = int(df.duplicated().sum())
    return {
        "row_count": row_count,
        "column_count": column_count,
        "missing_cells": missing_cells,
        "missing_pct": missing_pct,
        "duplicate_rows": duplicate_rows,
    }


def save_dataset_file(dataset_id: int, content: bytes) -> str:
    path = settings.DATASETS_DIR / f"dataset_{dataset_id}.csv"
    path.write_bytes(content)
    return str(path)


def load_dataset_dataframe(dataset: Dataset) -> pd.DataFrame:
    return pd.read_csv(dataset.file_path)


def build_preview(df: pd.DataFrame, limit: int) -> dict:
    limited = df.head(limit)
    # NaN is not valid JSON; convert to None.
    rows = limited.where(pd.notna(limited), None).to_dict(orient="records")
    return {"columns": list(df.columns), "rows": rows}


def _soh_histogram(soh_series: pd.Series) -> list[dict]:
    values = soh_series.dropna()
    bin_edges = np.arange(
        settings.SOH_HISTOGRAM_MIN,
        settings.SOH_HISTOGRAM_MAX + settings.SOH_HISTOGRAM_BIN_WIDTH,
        settings.SOH_HISTOGRAM_BIN_WIDTH,
    )
    counts, edges = np.histogram(values, bins=bin_edges)
    return [
        {"bin_start": float(edges[i]), "bin_end": float(edges[i + 1]), "count": int(counts[i])}
        for i in range(len(counts))
    ]


def build_data_quality(dataset_id: int, df: pd.DataFrame) -> dict:
    row_count = len(df)
    label_col = settings.LABEL_SOURCE_COLUMN

    labelled_df, dropped_missing_label = labeling.drop_missing_label(df)
    labelled_rows = len(labelled_df)
    duplicate_rows = int(df.duplicated().sum())

    classes = labeling.labels_from_soh(labelled_df[label_col])
    counts = classes.value_counts()
    class_distribution = [
        {"class": cls, "count": int(counts.get(cls, 0))} for cls in settings.SOH_CLASSES
    ]

    missing_by_column = []
    for col in df.columns:
        missing = int(df[col].isna().sum())
        missing_by_column.append(
            {
                "column": col,
                "missing": missing,
                "missing_pct": float(missing / row_count * 100) if row_count else 0.0,
            }
        )

    numeric_summary = []
    numeric_cols = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])]
    for col in numeric_cols:
        series = df[col].dropna()
        if len(series) == 0:
            continue
        numeric_summary.append(
            {
                "column": col,
                "min": float(series.min()),
                "max": float(series.max()),
                "mean": float(series.mean()),
                "std": float(series.std()) if len(series) > 1 else 0.0,
            }
        )

    soh_histogram = _soh_histogram(df[label_col])
    excluded_columns = features.excluded_columns_report()

    return {
        "dataset_id": dataset_id,
        "row_count": row_count,
        "labelled_rows": labelled_rows,
        "dropped_missing_label": dropped_missing_label,
        "duplicate_rows": duplicate_rows,
        "class_distribution": class_distribution,
        "missing_by_column": missing_by_column,
        "numeric_summary": numeric_summary,
        "soh_histogram": soh_histogram,
        "excluded_columns": excluded_columns,
    }


def create_dataset_record(
    db: Session, name: str, filename: str, content: bytes, df: pd.DataFrame, uploaded_by_user_id: int | None
) -> Dataset:
    stats = compute_basic_stats(df)
    dataset = Dataset(
        name=name,
        filename=filename,
        file_path="",
        row_count=stats["row_count"],
        column_count=stats["column_count"],
        missing_cells=stats["missing_cells"],
        missing_pct=stats["missing_pct"],
        duplicate_rows=stats["duplicate_rows"],
        uploaded_at=datetime.now(timezone.utc),
        status="ready",
        message=None,
        uploaded_by_user_id=uploaded_by_user_id,
    )
    db.add(dataset)
    db.flush()  # assign dataset.id
    dataset.file_path = save_dataset_file(dataset.id, content)
    db.commit()
    db.refresh(dataset)
    return dataset
