import random

import numpy as np
import pandas as pd
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.core.security import hash_password
from app.db.base import Base
from app.db.session import get_db
from app.main import app


def build_sample_dataframe(n_per_class: int = 15) -> pd.DataFrame:
    """A small synthetic dataframe shaped like the real CSV: it carries every
    blocklisted/leakage column (with plausible, correlated values) PLUS
    legitimate feature columns, with some missing values sprinkled in so
    preprocessing is actually exercised. Deterministic (seeded).
    """
    rng = random.Random(123)
    rows = []
    bands = {
        "GOOD": (85.0, 100.0),
        "MONITOR": (70.0, 84.9),
        "CRITICAL": (40.0, 69.9),
    }
    brands = ["Ford", "Tata", "BYD", "Nissan"]
    chemistries = ["NMC", "LFP", "NCA"]

    idx = 0
    for cls, (lo, hi) in bands.items():
        for _ in range(n_per_class):
            soh = round(rng.uniform(lo, hi), 2)
            capacity_loss = round(100.0 - soh, 2)  # exact algebraic identity, like the real data
            capacity_kwh = round(rng.uniform(40.0, 90.0), 1)
            remaining_capacity = round(capacity_kwh * soh / 100.0, 2)
            rows.append(
                {
                    "vehicle_id": f"EVTEST{idx:04d}",
                    "battery_serial": f"BATTEST{idx:04d}",
                    "vehicle_brand": rng.choice(brands),
                    "battery_chemistry": rng.choice(chemistries),
                    "battery_capacity_kwh": capacity_kwh,
                    "cycle_count": rng.uniform(100, 2000),
                    "internal_resistance": rng.uniform(0.01, 0.2),
                    "aging_score": rng.uniform(0, 100),
                    "charge_efficiency": rng.uniform(80, 99),
                    "state_of_health": soh,
                    "battery_health_percent": soh,  # restatement of the label
                    "capacity_loss_percent": capacity_loss,  # algebraic identity
                    "remaining_capacity": remaining_capacity,  # reconstructs label by ratio
                    "battery_failure": 1 if cls == "CRITICAL" and rng.random() < 0.3 else 0,
                }
            )
            idx += 1

    df = pd.DataFrame(rows)

    # Sprinkle missing values into feature columns so imputation is exercised.
    rng2 = np.random.default_rng(7)
    for col in ["cycle_count", "internal_resistance", "charge_efficiency", "aging_score", "battery_chemistry"]:
        mask = rng2.random(len(df)) < 0.1
        df.loc[mask, col] = np.nan

    return df


def build_sample_dataframe_with_missing_labels(n_per_class: int = 10, n_missing_label: int = 5) -> pd.DataFrame:
    df = build_sample_dataframe(n_per_class)
    df = df.sample(frac=1, random_state=1).reset_index(drop=True)
    df.loc[: n_missing_label - 1, "state_of_health"] = np.nan
    return df


@pytest.fixture()
def sample_df() -> pd.DataFrame:
    return build_sample_dataframe()


@pytest.fixture()
def sample_df_with_missing_labels() -> pd.DataFrame:
    return build_sample_dataframe_with_missing_labels()


@pytest.fixture()
def db_engine(tmp_path):
    db_path = tmp_path / "test.db"
    engine = create_engine(f"sqlite:///{db_path}", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    yield engine
    engine.dispose()


@pytest.fixture()
def tmp_storage_dirs(tmp_path, monkeypatch):
    models_dir = tmp_path / "models"
    datasets_dir = tmp_path / "datasets"
    models_dir.mkdir()
    datasets_dir.mkdir()
    monkeypatch.setattr(settings, "MODELS_DIR", models_dir)
    monkeypatch.setattr(settings, "DATASETS_DIR", datasets_dir)
    return tmp_path


@pytest.fixture()
def client(db_engine, tmp_storage_dirs):
    testing_session_local = sessionmaker(bind=db_engine, autoflush=False, autocommit=False)

    def override_get_db():
        db = testing_session_local()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture()
def db_session(db_engine):
    testing_session_local = sessionmaker(bind=db_engine, autoflush=False, autocommit=False)
    session = testing_session_local()
    yield session
    session.close()


TEST_PASSWORD = "testpass123"


@pytest.fixture()
def seeded_users(db_session):
    from app.models.user import User

    users = {}
    for role, email in [
        ("data_scientist", "scientist@test.io"),
        ("technician", "tech@test.io"),
        ("ev_user", "ev@test.io"),
    ]:
        user = User(email=email, name=role, role=role, password_hash=hash_password(TEST_PASSWORD))
        db_session.add(user)
        db_session.flush()
        users[role] = {"id": user.id, "email": email}
    db_session.commit()
    return users


def auth_header(client: TestClient, email: str, password: str = TEST_PASSWORD) -> dict:
    response = client.post("/api/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200, response.text
    token = response.json()["token"]
    return {"Authorization": f"Bearer {token}"}
