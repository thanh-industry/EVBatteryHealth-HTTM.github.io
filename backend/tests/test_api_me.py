"""EV User (role: ev_user) endpoints. ARCHITECTURE.md 4.8 is explicit that
this response must NOT expose ML internals - no algorithm, hyperparameters,
or confusion_matrix keys anywhere in the payload.
"""
import json

from app.models.battery import Battery
from app.models.vehicle import Vehicle
from tests.conftest import auth_header, build_sample_dataframe
from tests.test_api_vehicles_diagnostics import _create_vehicle_with_battery


_FORBIDDEN_ML_SUBSTRINGS = [
    "algorithm",
    "hyperparameter",
    "confusion_matrix",
    "n_estimators",
    "max_depth",
    "feature_importance",
    "supports_probability",
]


def test_me_battery_has_no_ml_internals(client, seeded_users, db_session):
    df = build_sample_dataframe(n_per_class=1)
    row = df.iloc[0]
    vehicle, _battery = _create_vehicle_with_battery(
        db_session, row, "EVOWNED1", owner_user_id=seeded_users["ev_user"]["id"]
    )

    headers = auth_header(client, "ev@test.io")
    response = client.get("/api/me/battery", headers=headers)
    assert response.status_code == 200

    body = response.json()
    assert set(body.keys()) == {
        "vehicle",
        "battery",
        "current_soh",
        "health_class",
        "last_checked_at",
        "soh_change_30d",
        "recommendation",
        "history",
    }

    flat = json.dumps(body)
    for forbidden in _FORBIDDEN_ML_SUBSTRINGS:
        assert forbidden not in flat, f"ML internal leaked into /api/me/battery: {forbidden}"


def test_me_battery_history_and_maintenance(client, seeded_users, db_session):
    df = build_sample_dataframe(n_per_class=1)
    row = df.iloc[0]
    _create_vehicle_with_battery(
        db_session, row, "EVOWNED2", owner_user_id=seeded_users["ev_user"]["id"]
    )

    headers = auth_header(client, "ev@test.io")

    history = client.get("/api/me/battery/history", headers=headers)
    assert history.status_code == 200
    assert isinstance(history.json(), list)

    maintenance = client.get("/api/me/maintenance", headers=headers)
    assert maintenance.status_code == 200
    assert isinstance(maintenance.json(), list)


def test_me_battery_404_when_no_vehicle_owned(client, seeded_users):
    headers = auth_header(client, "ev@test.io")
    response = client.get("/api/me/battery", headers=headers)
    assert response.status_code == 404


def test_me_battery_forbidden_for_technician(client, seeded_users):
    headers = auth_header(client, "tech@test.io")
    response = client.get("/api/me/battery", headers=headers)
    assert response.status_code == 403


def test_battery_lookup_is_case_insensitive_for_both_code_types(client, seeded_users, db_session):
    df = build_sample_dataframe(n_per_class=1)
    row = df.iloc[0]
    vehicle, battery = _create_vehicle_with_battery(db_session, row, "EVCASE1")

    headers = auth_header(client, "tech@test.io")

    by_vehicle_code = client.get(f"/api/batteries/lookup?code={vehicle.vehicle_code.lower()}", headers=headers)
    assert by_vehicle_code.status_code == 200
    assert by_vehicle_code.json()["vehicle"]["vehicle_code"] == "EVCASE1"

    by_serial = client.get(f"/api/batteries/lookup?code={battery.serial.upper()}", headers=headers)
    assert by_serial.status_code == 200
    assert by_serial.json()["battery"]["serial"] == battery.serial

    unknown = client.get("/api/batteries/lookup?code=DOES-NOT-EXIST", headers=headers)
    assert unknown.status_code == 404
    assert "detail" in unknown.json()
