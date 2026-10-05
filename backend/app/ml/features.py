"""Column classification and leakage blocklist enforcement.

This is the single place that decides what may enter a feature matrix. Every
other module (training, prediction, data-quality reporting) must go through
`build_feature_frame` rather than re-deriving its own column list.
"""
import pandas as pd

from app.core.config import settings


def _blocked_columns() -> set[str]:
    """Every column that must never reach a feature matrix: the leakage
    blocklist, the label source itself, and the derived label column name
    (settings.DERIVED_LABEL_COLUMN) used transiently while seeding. Single
    source of truth shared by build_feature_frame and assert_no_leakage.
    """
    return set(settings.LEAKAGE_BLOCKLIST) | {
        settings.LABEL_SOURCE_COLUMN,
        settings.DERIVED_LABEL_COLUMN,
    }


def excluded_columns_report() -> list[dict]:
    """The leakage blocklist with reasons, for the data-quality endpoint."""
    return [
        {"column": col, "reason": settings.LEAKAGE_REASONS.get(col, "excluded")}
        for col in settings.LEAKAGE_BLOCKLIST
    ]


def build_feature_frame(df: pd.DataFrame) -> pd.DataFrame:
    """Drop the label column and every blocklisted column.

    Returns a new DataFrame containing only columns that are legitimate model
    inputs (physical sensor readings, BMS telemetry, vehicle specs, driving /
    charging behaviour). Any column not explicitly blocklisted or the label
    source is kept.

    Also drops settings.DERIVED_LABEL_COLUMN ("health_class") if present -
    that column never exists in the real CSV, but seeding transiently adds it
    to a working frame to stratify-sample rows per class, and it must never
    ride along into a feature snapshot or a training frame.
    """
    drop_cols = _blocked_columns()
    keep_cols = [c for c in df.columns if c not in drop_cols]
    return df[keep_cols].copy()


def split_numeric_categorical(df: pd.DataFrame) -> tuple[list[str], list[str]]:
    """Split a feature frame's columns into numeric and categorical lists."""
    numeric_cols = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])]
    categorical_cols = [c for c in df.columns if c not in numeric_cols]
    return numeric_cols, categorical_cols


def assert_no_leakage(df: pd.DataFrame) -> None:
    """Defensive check usable by tests and by training itself before fit."""
    leaked = set(df.columns) & _blocked_columns()
    if leaked:
        raise ValueError(f"Leakage columns present in feature frame: {sorted(leaked)}")


def feature_dict_from_row(df_row: pd.DataFrame) -> dict:
    """Build a JSON-safe {column: value} dict of feature columns for a single
    row DataFrame. Used by seeding to snapshot a CSV row's feature vector.
    """
    record = build_feature_frame(df_row).iloc[0].to_dict()
    safe: dict = {}
    for key, value in record.items():
        if pd.isna(value):
            safe[key] = None
        elif hasattr(value, "item"):
            safe[key] = value.item()
        else:
            safe[key] = value
    return safe
