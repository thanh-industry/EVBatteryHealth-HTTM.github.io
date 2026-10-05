"""Regression coverage for the health_class leak found in orchestrator
review: seed.py's row selection used to leave a derived "health_class"
column attached to each row, which then rode into feature_snapshot_json
(64 keys instead of 63). This exercises the real seed.py code path end to
end against the real CSV, not a synthetic stand-in.
"""
import pandas as pd

from app.core.config import settings
from app.ml import features
from app.seed import select_seed_rows


def test_select_seed_rows_drops_derived_label_column():
    raw_df = pd.read_csv(settings.SOURCE_CSV_PATH)
    rows = select_seed_rows(raw_df)

    assert settings.DERIVED_LABEL_COLUMN not in rows.columns
    assert len(rows) > 0


def test_seed_row_feature_snapshot_has_no_label_columns():
    raw_df = pd.read_csv(settings.SOURCE_CSV_PATH)
    rows = select_seed_rows(raw_df)

    # LABEL_SOURCE_COLUMN ("state_of_health") is already one of the
    # LEAKAGE_BLOCKLIST entries, so it is not subtracted a second time.
    expected_feature_count = raw_df.shape[1] - len(settings.LEAKAGE_BLOCKLIST)

    for _, row in rows.head(5).iterrows():
        snapshot = features.feature_dict_from_row(pd.DataFrame([row]))
        assert settings.DERIVED_LABEL_COLUMN not in snapshot
        assert settings.LABEL_SOURCE_COLUMN not in snapshot
        for col in settings.LEAKAGE_BLOCKLIST:
            assert col not in snapshot
        assert len(snapshot) == expected_feature_count
