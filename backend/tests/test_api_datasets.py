import io

from tests.conftest import auth_header, build_sample_dataframe


def _csv_bytes() -> bytes:
    df = build_sample_dataframe(n_per_class=10)
    return df.to_csv(index=False).encode("utf-8")


def test_upload_rejects_non_csv_extension(client, seeded_users):
    headers = auth_header(client, "scientist@test.io")
    response = client.post(
        "/api/datasets/upload",
        files={"file": ("data.txt", io.BytesIO(b"hello"), "text/plain")},
        headers=headers,
    )
    assert response.status_code == 400
    assert "csv" in response.json()["detail"].lower()


def test_upload_rejects_empty_file(client, seeded_users):
    headers = auth_header(client, "scientist@test.io")
    response = client.post(
        "/api/datasets/upload",
        files={"file": ("empty.csv", io.BytesIO(b""), "text/csv")},
        headers=headers,
    )
    assert response.status_code == 400
    assert "empty" in response.json()["detail"].lower()


def test_upload_rejects_unparseable_csv(client, seeded_users):
    headers = auth_header(client, "scientist@test.io")
    garbage = b'"unterminated quote,field\n"another,row'
    response = client.post(
        "/api/datasets/upload",
        files={"file": ("bad.csv", io.BytesIO(garbage), "text/csv")},
        headers=headers,
    )
    assert response.status_code == 400


def test_upload_rejects_csv_missing_label_column(client, seeded_users):
    headers = auth_header(client, "scientist@test.io")
    csv_bytes = b"a,b,c\n1,2,3\n4,5,6\n"
    response = client.post(
        "/api/datasets/upload",
        files={"file": ("nolabel.csv", io.BytesIO(csv_bytes), "text/csv")},
        headers=headers,
    )
    assert response.status_code == 400
    assert "state_of_health" in response.json()["detail"]


def test_upload_succeeds_for_valid_csv(client, seeded_users):
    headers = auth_header(client, "scientist@test.io")
    response = client.post(
        "/api/datasets/upload",
        files={"file": ("good.csv", io.BytesIO(_csv_bytes()), "text/csv")},
        headers=headers,
    )
    assert response.status_code == 201, response.text
    body = response.json()
    assert body["status"] == "ready"
    assert body["row_count"] == 30
    assert body["message"] is None


def test_upload_requires_authentication(client, seeded_users):
    response = client.post(
        "/api/datasets/upload",
        files={"file": ("good.csv", io.BytesIO(_csv_bytes()), "text/csv")},
    )
    assert response.status_code == 401


def test_upload_rejects_wrong_role(client, seeded_users):
    headers = auth_header(client, "tech@test.io")
    response = client.post(
        "/api/datasets/upload",
        files={"file": ("good.csv", io.BytesIO(_csv_bytes()), "text/csv")},
        headers=headers,
    )
    assert response.status_code == 403


def test_get_unknown_dataset_is_404(client, seeded_users):
    headers = auth_header(client, "scientist@test.io")
    response = client.get("/api/datasets/999999", headers=headers)
    assert response.status_code == 404


def test_quality_report_shape(client, seeded_users):
    headers = auth_header(client, "scientist@test.io")
    upload = client.post(
        "/api/datasets/upload",
        files={"file": ("good.csv", io.BytesIO(_csv_bytes()), "text/csv")},
        headers=headers,
    )
    dataset_id = upload.json()["id"]

    response = client.get(f"/api/datasets/{dataset_id}/quality", headers=headers)
    assert response.status_code == 200
    quality = response.json()
    assert quality["row_count"] == 30
    classes = {item["class"] for item in quality["class_distribution"]}
    assert classes == {"GOOD", "MONITOR", "CRITICAL"}
    excluded = {item["column"] for item in quality["excluded_columns"]}
    assert "state_of_health" in excluded
    assert "vehicle_id" in excluded


def test_delete_dataset_then_404(client, seeded_users):
    headers = auth_header(client, "scientist@test.io")
    upload = client.post(
        "/api/datasets/upload",
        files={"file": ("good.csv", io.BytesIO(_csv_bytes()), "text/csv")},
        headers=headers,
    )
    dataset_id = upload.json()["id"]

    delete_response = client.delete(f"/api/datasets/{dataset_id}", headers=headers)
    assert delete_response.status_code == 204

    get_response = client.get(f"/api/datasets/{dataset_id}", headers=headers)
    assert get_response.status_code == 404
