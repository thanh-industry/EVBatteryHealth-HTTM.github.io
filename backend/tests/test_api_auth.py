from tests.conftest import TEST_PASSWORD, auth_header


def test_login_success_each_role(client, seeded_users):
    for role, info in seeded_users.items():
        response = client.post(
            "/api/auth/login", json={"email": info["email"], "password": TEST_PASSWORD}
        )
        assert response.status_code == 200
        body = response.json()
        assert body["user"]["role"] == role
        assert body["token"]


def test_login_wrong_password_401(client, seeded_users):
    response = client.post(
        "/api/auth/login", json={"email": "scientist@test.io", "password": "wrong-password"}
    )
    assert response.status_code == 401
    assert "detail" in response.json()


def test_login_unknown_email_401(client, seeded_users):
    response = client.post(
        "/api/auth/login", json={"email": "nobody@test.io", "password": TEST_PASSWORD}
    )
    assert response.status_code == 401


def test_me_returns_current_user(client, seeded_users):
    headers = auth_header(client, "scientist@test.io")
    response = client.get("/api/auth/me", headers=headers)
    assert response.status_code == 200
    assert response.json()["email"] == "scientist@test.io"


def test_me_requires_authentication(client, seeded_users):
    response = client.get("/api/auth/me")
    assert response.status_code == 401


def test_me_rejects_garbage_token(client, seeded_users):
    response = client.get("/api/auth/me", headers={"Authorization": "Bearer not-a-real-token"})
    assert response.status_code == 401


def test_thresholds_endpoint_matches_config(client, seeded_users):
    response = client.get("/api/config/thresholds")
    assert response.status_code == 200
    assert response.json() == {"good_min": 85.0, "monitor_min": 70.0}
