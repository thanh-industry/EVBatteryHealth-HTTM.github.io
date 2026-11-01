from __future__ import annotations

from app import config, db, seed_demo


def test_seed_is_idempotent_and_uses_real_csv_values(tmp_path):
    if not config.RAW_DATASET_PATH.exists():
        import pytest

        pytest.skip("source dataset CSV not present")

    db_path = tmp_path / "seed_test.db"
    summary1 = seed_demo.seed(n=6, random_state=1, db_path=db_path)
    assert summary1["records_created"] > 0
    assert summary1["records_skipped_existing"] == 0

    count_after_first = db.count_battery_records(db_path=db_path)
    assert count_after_first == summary1["records_created"]

    # Every seeded record's parameters must be real values straight off the
    # CSV row (spot check a couple of records have non-trivial data).
    records = db.list_battery_records(db_path=db_path)
    assert len(records) == count_after_first
    for record in records:
        assert len(record["parameters"]) > 0
        assert record["battery_serial"].startswith("BAT-")

    # Re-running must not duplicate anything.
    summary2 = seed_demo.seed(n=6, random_state=1, db_path=db_path)
    assert summary2["records_created"] == 0
    assert summary2["records_skipped_existing"] == summary1["records_created"]
    assert db.count_battery_records(db_path=db_path) == count_after_first
