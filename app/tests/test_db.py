from __future__ import annotations

import pytest

from app import db


def _params(**overrides):
    base = {"battery_health_percent": 80.0, "cycle_count": 500.0}
    base.update(overrides)
    return base


def test_create_and_get_record(db_path):
    rid = db.create_battery_record("BAT-0001", "EV0001", _params(), db_path=db_path)
    record = db.get_battery_record(rid, db_path=db_path)
    assert record is not None
    assert record["battery_serial"] == "BAT-0001"
    assert record["vehicle_id"] == "EV0001"
    assert record["parameters"]["battery_health_percent"] == 80.0


def test_duplicate_serial_rejected(db_path):
    db.create_battery_record("BAT-0001", "EV0001", _params(), db_path=db_path)
    with pytest.raises(ValueError):
        db.create_battery_record("BAT-0001", "EV0002", _params(), db_path=db_path)


def test_update_record(db_path):
    rid = db.create_battery_record("BAT-0001", "EV0001", _params(), db_path=db_path)
    ok = db.update_battery_record(
        rid, vehicle_id="EV9999", parameters=_params(cycle_count=999.0), db_path=db_path
    )
    assert ok is True
    record = db.get_battery_record(rid, db_path=db_path)
    assert record["vehicle_id"] == "EV9999"
    assert record["parameters"]["cycle_count"] == 999.0


def test_update_missing_record_returns_false(db_path):
    assert db.update_battery_record(999, vehicle_id="X", db_path=db_path) is False


def test_search_by_serial(db_path):
    db.create_battery_record("BAT-ALPHA", "EV0001", _params(), db_path=db_path)
    db.create_battery_record("BAT-BETA", "EV0002", _params(), db_path=db_path)
    results = db.search_battery_records("alpha", db_path=db_path)
    assert len(results) == 1
    assert results[0]["battery_serial"] == "BAT-ALPHA"


def test_search_by_vehicle_id(db_path):
    db.create_battery_record("BAT-ALPHA", "EV0001", _params(), db_path=db_path)
    db.create_battery_record("BAT-BETA", "EV0002", _params(), db_path=db_path)
    results = db.search_battery_records("ev0002", db_path=db_path)
    assert len(results) == 1
    assert results[0]["vehicle_id"] == "EV0002"


def test_search_empty_query_lists_all(db_path):
    db.create_battery_record("BAT-ALPHA", "EV0001", _params(), db_path=db_path)
    db.create_battery_record("BAT-BETA", "EV0002", _params(), db_path=db_path)
    results = db.search_battery_records("", db_path=db_path)
    assert len(results) == 2


def test_count_battery_records(db_path):
    assert db.count_battery_records(db_path=db_path) == 0
    db.create_battery_record("BAT-ALPHA", "EV0001", _params(), db_path=db_path)
    assert db.count_battery_records(db_path=db_path) == 1


def test_classification_and_assessment_link(db_path):
    rid = db.create_battery_record("BAT-0001", "EV0001", _params(), db_path=db_path)
    cid = db.create_classification(
        battery_record_id=rid,
        prediction=1,
        prediction_label="Failure",
        probability=0.87,
        model_algorithm="logistic_regression",
        model_trained_at="2026-01-01T00:00:00",
        input_snapshot=_params(),
        db_path=db_path,
    )
    classification = db.get_classification(cid, db_path=db_path)
    assert classification["prediction"] == 1
    assert classification["prediction_label"] == "Failure"
    assert classification["probability"] == pytest.approx(0.87)

    aid = db.create_assessment(
        classification_id=cid,
        assessment="High risk observed.",
        recommendation="Inspect within 7 days.",
        assessed_by="Tech A",
        db_path=db_path,
    )
    assessment = db.get_assessment_for_classification(cid, db_path=db_path)
    assert assessment is not None
    assert assessment["id"] == aid
    assert assessment["assessment"] == "High risk observed."


def test_assessment_unique_per_classification(db_path):
    rid = db.create_battery_record("BAT-0001", "EV0001", _params(), db_path=db_path)
    cid = db.create_classification(
        battery_record_id=rid,
        prediction=0,
        prediction_label="No Failure",
        probability=None,
        model_algorithm="svm",
        model_trained_at="2026-01-01T00:00:00",
        input_snapshot=_params(),
        db_path=db_path,
    )
    db.create_assessment(cid, "ok", "none needed", db_path=db_path)
    with pytest.raises(ValueError):
        db.create_assessment(cid, "again", "still none", db_path=db_path)


def test_classification_history_ordering_and_filters(db_path):
    r1 = db.create_battery_record("BAT-0001", "EV0001", _params(), db_path=db_path)
    r2 = db.create_battery_record("BAT-0002", "EV0002", _params(), db_path=db_path)

    c1 = db.create_classification(
        r1, 0, "No Failure", 0.1, "svm", "t", _params(), db_path=db_path
    )
    c2 = db.create_classification(
        r2, 1, "Failure", 0.9, "svm", "t", _params(), db_path=db_path
    )
    db.create_assessment(c2, "bad", "fix it", db_path=db_path)

    history = db.list_classification_history(db_path=db_path)
    assert len(history) == 2
    # newest first: c2 was created after c1
    assert history[0]["classification_id"] == c2
    assert history[0]["assessment_id"] is not None
    assert history[1]["classification_id"] == c1
    assert history[1]["assessment_id"] is None

    filtered = db.list_classification_history(serial="0002", db_path=db_path)
    assert len(filtered) == 1
    assert filtered[0]["battery_serial"] == "BAT-0002"

    filtered_vehicle = db.list_classification_history(vehicle_id="EV0001", db_path=db_path)
    assert len(filtered_vehicle) == 1
    assert filtered_vehicle[0]["vehicle_id"] == "EV0001"


def test_list_classifications_for_record(db_path):
    rid = db.create_battery_record("BAT-0001", "EV0001", _params(), db_path=db_path)
    db.create_classification(rid, 0, "No Failure", 0.2, "svm", "t", _params(), db_path=db_path)
    db.create_classification(rid, 1, "Failure", 0.8, "svm", "t", _params(), db_path=db_path)
    results = db.list_classifications_for_record(rid, db_path=db_path)
    assert len(results) == 2
    assert db.count_classifications(db_path=db_path) == 2
