import pytest

from app.core.config import settings
from app.ml import features


def test_no_leakage_columns(sample_df):
    """The single most important test in the suite: every blocklisted column
    (plus the label source itself) must be absent from the built feature
    matrix, even though the raw input dataframe carries all of them.
    """
    assert set(settings.LEAKAGE_BLOCKLIST).issubset(sample_df.columns)

    feature_frame = features.build_feature_frame(sample_df)

    for col in settings.LEAKAGE_BLOCKLIST:
        assert col not in feature_frame.columns, f"leaked column: {col}"
    assert settings.LABEL_SOURCE_COLUMN not in feature_frame.columns

    # Legitimate feature columns must still be present.
    assert "internal_resistance" in feature_frame.columns
    assert "aging_score" in feature_frame.columns
    assert "battery_capacity_kwh" in feature_frame.columns


def test_assert_no_leakage_raises_on_violation(sample_df):
    with pytest.raises(ValueError):
        features.assert_no_leakage(sample_df)


def test_assert_no_leakage_passes_on_clean_frame(sample_df):
    clean = features.build_feature_frame(sample_df)
    features.assert_no_leakage(clean)  # must not raise


def test_excluded_columns_report_matches_blocklist():
    report = features.excluded_columns_report()
    reported_cols = {item["column"] for item in report}
    assert reported_cols == set(settings.LEAKAGE_BLOCKLIST)
    for item in report:
        assert item["reason"]  # every exclusion has a real reason, not empty


def test_derived_label_column_is_excluded_from_feature_frame(sample_df):
    """Regression test for the health_class leak found in review: a derived
    label column (added transiently by seeding to stratify-sample rows per
    class) must never ride along into a feature matrix or a snapshot, even
    though it is neither in LEAKAGE_BLOCKLIST nor the raw label source.
    """
    tainted = sample_df.copy()
    tainted[settings.DERIVED_LABEL_COLUMN] = "GOOD"
    assert settings.DERIVED_LABEL_COLUMN in tainted.columns

    feature_frame = features.build_feature_frame(tainted)
    assert settings.DERIVED_LABEL_COLUMN not in feature_frame.columns

    with pytest.raises(ValueError):
        features.assert_no_leakage(tainted)


def test_feature_dict_from_row_excludes_label_and_derived_label(sample_df):
    """Same regression, exercised through the exact function seed.py calls
    to build a battery's feature_snapshot_json.
    """
    row = sample_df.iloc[[0]].copy()
    row[settings.DERIVED_LABEL_COLUMN] = "CRITICAL"

    snapshot = features.feature_dict_from_row(row)

    assert settings.DERIVED_LABEL_COLUMN not in snapshot
    assert settings.LABEL_SOURCE_COLUMN not in snapshot
    for col in settings.LEAKAGE_BLOCKLIST:
        assert col not in snapshot
