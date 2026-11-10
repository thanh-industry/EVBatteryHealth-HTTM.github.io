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


def test_history_seeding_builds_a_usable_trend_and_keeps_today_genuine(tmp_path):
    """Prior inspections exist so the trend panel has something to draw. The
    most recent reading must remain the untouched CSV row; only earlier ones
    are derived."""
    from app import model_service, trend

    db_path = tmp_path / "history.db"
    summary = seed_demo.seed(n=4, db_path=db_path, history=3, history_records=2)

    if not summary["model_deployed"]:
        pytest.skip("no model deployed; history seeding needs one to classify")

    records = db.list_battery_records(limit=10, db_path=db_path)
    with_history = [
        r for r in records
        if len(db.list_classifications_for_record(r["id"], db_path=db_path)) > 1
    ]
    assert with_history, "expected at least one record with prior inspections"

    record = with_history[0]
    history = db.list_classifications_for_record(record["id"], db_path=db_path)
    assert len(history) == 4  # 3 derived + 1 present-day

    oldest_first = sorted(history, key=lambda c: c["created_at"])
    # Earlier inspections are strictly older than the present-day reading.
    assert oldest_first[0]["created_at"] < oldest_first[-1]["created_at"]

    # The newest snapshot must equal the record's stored (genuine) parameters.
    newest_snapshot = oldest_first[-1]["input_snapshot"]
    for name, value in record["parameters"].items():
        assert newest_snapshot[name] == value, (
            f"{name} differs: history seeding must not alter the present-day "
            "reading taken from the real CSV row"
        )

    series = trend.build_trends(history)
    assert series, "seeded history should produce at least one trend series"
    soh = [s for s in series if s.metric.key == "state_of_health"]
    if soh:
        values = [p.value for p in soh[0].points]
        assert values == sorted(values, reverse=True), (
            "derived history should age coherently: health declines over time"
        )


def test_history_zero_seeds_only_the_present_day_reading(tmp_path):
    db_path = tmp_path / "nohistory.db"
    summary = seed_demo.seed(n=3, db_path=db_path, history=0)
    if not summary["model_deployed"]:
        pytest.skip("no model deployed")
    for record in db.list_battery_records(limit=10, db_path=db_path):
        assert len(db.list_classifications_for_record(record["id"], db_path=db_path)) <= 1
