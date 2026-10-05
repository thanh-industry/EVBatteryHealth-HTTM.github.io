import io
import json
from datetime import datetime, timezone

from app.ml import features
from app.models.battery import Battery
from app.models.measurement import BatteryMeasurement
from app.models.vehicle import Vehicle
from tests.conftest import auth_header, build_sample_dataframe


def _create_vehicle_with_battery(db_session, row, vehicle_code, owner_user_id=None):
    snapshot = features.feature_dict_from_row(row.to_frame().T)
    battery = Battery(
        serial=str(row["battery_serial"]),
        manufacturer="TestMfg",
        chemistry="NMC",
        capacity_kwh=float(row["battery_capacity_kwh"]),
        cycle_count=float(row["cycle_count"]) if row["cycle_count"] == row["cycle_count"] else None,
        current_soh=float(row["state_of_health"]),
        feature_snapshot_json=json.dumps(snapshot),
    )
    db_session.add(battery)
    db_session.flush()

    vehicle = Vehicle(
        vehicle_code=vehicle_code,
        brand=str(row["vehicle_brand"]),
        model="TestModel",
        vehicle_type="Sedan",
        manufacturing_year=2020,
        drive_type="FWD",
        odometer_km=10000.0,
        fleet_or_private="Private",
        battery_id=battery.id,
        owner_user_id=owner_user_id,
    )
    db_session.add(vehicle)
    db_session.flush()

    measurement = BatteryMeasurement(
        battery_id=battery.id,
        recorded_at=datetime.now(timezone.utc),
        soh=float(row["state_of_health"]),
        state_of_charge=50.0,
        internal_resistance=float(row["internal_resistance"]) if row["internal_resistance"] == row["internal_resistance"] else 0.05,
        cell_voltage_avg=3.7,
        cell_temperature_avg=25.0,
        cell_temperature_max=30.0,
        charge_efficiency=90.0,
        cycle_count=float(row["cycle_count"]) if row["cycle_count"] == row["cycle_count"] else 100.0,
    )
    db_session.add(measurement)
    db_session.commit()
    return vehicle, battery


def _train_and_deploy(client, headers) -> int:
    df = build_sample_dataframe(n_per_class=10)
    csv_bytes = df.to_csv(index=False).encode("utf-8")
    upload = client.post(
        "/api/datasets/upload",
        files={"file": ("sample.csv", io.BytesIO(csv_bytes), "text/csv")},
        headers=headers,
    )
    dataset_id = upload.json()["id"]
    run = client.post(
        "/api/training/runs",
        json={"dataset_id": dataset_id, "algorithm": "random_forest"},
        headers=headers,
    ).json()
    client.post(f"/api/models/{run['id']}/deploy", headers=headers)
    return run["id"]


def test_get_unknown_vehicle_code_is_404(client, seeded_users):
    headers = auth_header(client, "tech@test.io")
    response = client.get("/api/vehicles/NOPE123", headers=headers)
    assert response.status_code == 404


def test_battery_lookup_unknown_code_is_404(client, seeded_users):
    headers = auth_header(client, "tech@test.io")
    response = client.get("/api/batteries/lookup?code=NOPE123", headers=headers)
    assert response.status_code == 404


def test_vehicles_forbidden_for_data_scientist(client, seeded_users):
    headers = auth_header(client, "scientist@test.io")
    response = client.get("/api/vehicles", headers=headers)
    assert response.status_code == 403


def test_diagnostic_409_when_no_model_deployed(client, seeded_users, db_session):
    df = build_sample_dataframe(n_per_class=1)
    row = df.iloc[0]
    _create_vehicle_with_battery(db_session, row, "EVNODEPLOY1")

    headers = auth_header(client, "tech@test.io")
    response = client.post("/api/diagnostics", json={"code": "EVNODEPLOY1"}, headers=headers)
    assert response.status_code == 409
    assert "No model is currently deployed" in response.json()["detail"]


def test_diagnostic_404_unknown_code(client, seeded_users):
    headers = auth_header(client, "tech@test.io")
    response = client.post("/api/diagnostics", json={"code": "GHOSTCODE"}, headers=headers)
    assert response.status_code == 404


def test_diagnostic_409_after_deployment_deactivated(client, seeded_users, db_session):
    """A model was deployed and working, then gets deactivated (e.g. the
    data scientist deploys something else, or an admin un-deploys). The next
    diagnostic attempt must cleanly 409, not 500, even though a model WAS
    active moments ago.
    """
    from app.models.model_deployment import ModelDeployment

    headers_sci = auth_header(client, "scientist@test.io")
    _train_and_deploy(client, headers_sci)

    df = build_sample_dataframe(n_per_class=1)
    row = df.iloc[0]
    _create_vehicle_with_battery(db_session, row, "EVDEACTIVATED1")

    headers_tech = auth_header(client, "tech@test.io")
    ok_response = client.post("/api/diagnostics", json={"code": "EVDEACTIVATED1"}, headers=headers_tech)
    assert ok_response.status_code == 201

    db_session.query(ModelDeployment).filter(ModelDeployment.active.is_(True)).update({"active": False})
    db_session.commit()

    response = client.post("/api/diagnostics", json={"code": "EVDEACTIVATED1"}, headers=headers_tech)
    assert response.status_code == 409
    assert "No model is currently deployed" in response.json()["detail"]


def test_diagnostic_409_on_corrupt_model_artifact_not_500(client, seeded_users, db_session):
    """A corrupt/truncated joblib artifact must never surface a 500 stack
    trace to the client - it must degrade to a clean 409.
    """
    from app.models.training_run import TrainingRun

    headers_sci = auth_header(client, "scientist@test.io")
    run_id = _train_and_deploy(client, headers_sci)

    run = db_session.get(TrainingRun, run_id)
    with open(run.model_path, "wb") as f:
        f.write(b"not a valid joblib pickle file")

    df = build_sample_dataframe(n_per_class=1)
    row = df.iloc[0]
    _create_vehicle_with_battery(db_session, row, "EVCORRUPT1")

    headers_tech = auth_header(client, "tech@test.io")
    response = client.post("/api/diagnostics", json={"code": "EVCORRUPT1"}, headers=headers_tech)
    assert response.status_code == 409
    assert "detail" in response.json()
    assert "Traceback" not in response.text


def test_diagnostic_full_flow_after_deploy(client, seeded_users, db_session):
    headers_sci = auth_header(client, "scientist@test.io")
    _train_and_deploy(client, headers_sci)

    df = build_sample_dataframe(n_per_class=1)
    row = df.iloc[0]
    _create_vehicle_with_battery(db_session, row, "EVDEPLOYED1")

    headers_tech = auth_header(client, "tech@test.io")
    response = client.post(
        "/api/diagnostics", json={"code": "EVDEPLOYED1", "notes": "routine check"}, headers=headers_tech
    )
    assert response.status_code == 201, response.text
    diagnostic = response.json()
    assert diagnostic["predicted_class"] in ["GOOD", "MONITOR", "CRITICAL"]
    assert diagnostic["confidence"] is not None
    assert 0.0 <= diagnostic["confidence"] <= 1.0
    probs = {p["class"]: p["probability"] for p in diagnostic["class_probabilities"]}
    assert abs(sum(probs.values()) - 1.0) < 1e-6
    assert diagnostic["notes"] == "routine check"
    assert diagnostic["technician_name"] is not None
    assert diagnostic["recommendation"]

    # lookup by battery serial too
    lookup = client.get(
        f"/api/batteries/lookup?code={row['battery_serial']}", headers=headers_tech
    )
    assert lookup.status_code == 200
    assert lookup.json()["vehicle"]["vehicle_code"] == "EVDEPLOYED1"


def test_diagnostics_forbidden_for_ev_user(client, seeded_users, db_session):
    headers_sci = auth_header(client, "scientist@test.io")
    _train_and_deploy(client, headers_sci)

    headers_ev = auth_header(client, "ev@test.io")
    response = client.post("/api/diagnostics", json={"code": "ANY"}, headers=headers_ev)
    assert response.status_code == 403


def test_notifications_are_scoped_to_owner(client, seeded_users, db_session):
    from app.services import notification_service

    notification_service.create_notification(
        db_session,
        user_id=seeded_users["ev_user"]["id"],
        type_="system",
        severity="info",
        title="For EV user only",
        body="body",
    )
    notification_service.create_notification(
        db_session,
        user_id=seeded_users["technician"]["id"],
        type_="system",
        severity="info",
        title="For technician only",
        body="body",
    )

    headers_ev = auth_header(client, "ev@test.io")
    response = client.get("/api/notifications", headers=headers_ev)
    assert response.status_code == 200
    titles = [n["title"] for n in response.json()]
    assert "For EV user only" in titles
    assert "For technician only" not in titles
