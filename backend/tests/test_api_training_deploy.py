import io

from app.models.model_deployment import ModelDeployment
from tests.conftest import auth_header, build_sample_dataframe


def _upload_dataset(client, headers) -> int:
    df = build_sample_dataframe(n_per_class=10)
    csv_bytes = df.to_csv(index=False).encode("utf-8")
    response = client.post(
        "/api/datasets/upload",
        files={"file": ("sample.csv", io.BytesIO(csv_bytes), "text/csv")},
        headers=headers,
    )
    assert response.status_code == 201, response.text
    return response.json()["id"]


def test_training_run_end_to_end(client, seeded_users):
    headers = auth_header(client, "scientist@test.io")
    dataset_id = _upload_dataset(client, headers)

    response = client.post(
        "/api/training/runs",
        json={"dataset_id": dataset_id, "algorithm": "random_forest", "test_size": 0.3},
        headers=headers,
    )
    assert response.status_code == 201, response.text
    run = response.json()

    assert run["status"] == "completed"
    assert run["error"] is None
    assert run["dataset_id"] == dataset_id
    assert run["algorithm"] == "random_forest"
    assert run["metrics"] is not None
    assert 0.0 <= run["metrics"]["accuracy"] <= 1.0
    assert run["confusion_matrix"] is not None
    assert run["is_deployed"] is False
    assert run["version"] == f"v{run['id']}"
    assert run["supports_probability"] is True

    fetched = client.get(f"/api/training/runs/{run['id']}", headers=headers)
    assert fetched.status_code == 200
    assert fetched.json()["id"] == run["id"]


def test_training_run_unknown_dataset_404(client, seeded_users):
    headers = auth_header(client, "scientist@test.io")
    response = client.post(
        "/api/training/runs",
        json={"dataset_id": 999999, "algorithm": "random_forest"},
        headers=headers,
    )
    assert response.status_code == 404


def test_deploy_makes_exactly_one_model_active(client, seeded_users, db_session):
    headers = auth_header(client, "scientist@test.io")
    dataset_id = _upload_dataset(client, headers)

    run1 = client.post(
        "/api/training/runs",
        json={"dataset_id": dataset_id, "algorithm": "random_forest"},
        headers=headers,
    ).json()
    run2 = client.post(
        "/api/training/runs",
        json={"dataset_id": dataset_id, "algorithm": "logistic_regression"},
        headers=headers,
    ).json()

    deploy1 = client.post(f"/api/models/{run1['id']}/deploy", headers=headers)
    assert deploy1.status_code == 200
    assert deploy1.json()["run_id"] == run1["id"]

    active_count = db_session.query(ModelDeployment).filter(ModelDeployment.active.is_(True)).count()
    assert active_count == 1

    deploy2 = client.post(f"/api/models/{run2['id']}/deploy", headers=headers)
    assert deploy2.status_code == 200
    assert deploy2.json()["run_id"] == run2["id"]

    db_session.expire_all()
    active_rows = db_session.query(ModelDeployment).filter(ModelDeployment.active.is_(True)).all()
    assert len(active_rows) == 1
    assert active_rows[0].run_id == run2["id"]

    active_response = client.get("/api/models/active", headers=headers)
    assert active_response.json()["run_id"] == run2["id"]


def test_deploy_unknown_run_404(client, seeded_users):
    headers = auth_header(client, "scientist@test.io")
    response = client.post("/api/models/999999/deploy", headers=headers)
    assert response.status_code == 404


def test_active_model_null_when_none_deployed(client, seeded_users):
    headers = auth_header(client, "scientist@test.io")
    response = client.get("/api/models/active", headers=headers)
    assert response.status_code == 200
    assert response.json() is None


def test_models_list_role_forbidden_for_technician(client, seeded_users):
    headers = auth_header(client, "tech@test.io")
    response = client.get("/api/models", headers=headers)
    assert response.status_code == 403
