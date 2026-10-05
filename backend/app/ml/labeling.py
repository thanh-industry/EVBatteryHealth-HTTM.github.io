"""SoH -> class label. Reads ONLY config.SOH_GOOD_MIN / SOH_MONITOR_MIN.

Zero magic numbers anywhere else in the codebase - everything funnels through
soh_to_class().
"""
import pandas as pd

from app.core.config import settings


def soh_to_class(soh: float) -> str:
    if soh >= settings.SOH_GOOD_MIN:
        return "GOOD"
    if soh >= settings.SOH_MONITOR_MIN:
        return "MONITOR"
    return "CRITICAL"


def labels_from_soh(soh_series: pd.Series) -> pd.Series:
    """Vectorised soh_to_class. Caller must drop nulls first (see
    drop_missing_label) - this function assumes no NaN remain.
    """
    return soh_series.map(soh_to_class)


def drop_missing_label(df: pd.DataFrame, label_column: str | None = None) -> tuple[pd.DataFrame, int]:
    """Drop rows with a null label source column. Returns (clean_df, dropped_count)."""
    label_column = label_column or settings.LABEL_SOURCE_COLUMN
    total = len(df)
    clean = df[df[label_column].notna()].copy()
    dropped = total - len(clean)
    return clean, dropped
