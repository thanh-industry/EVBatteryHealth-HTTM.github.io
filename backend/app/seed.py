"""Seed the database from the real CSV dataset.

Run with: python -m app.seed

Idempotent: if the demo data scientist account already exists, seeding is
skipped entirely so re-running is always safe.

Rule (ARCHITECTURE.md 6): seed real records, never fake metrics. Every
vehicle/battery/measurement value below is read from the real CSV. The one
place real numbers are *computed* rather than copied is the training run,
and that computation is a genuine call into app.ml.train.run_training - not
a hard-coded number.

The historical SoH measurement series per battery is a documented demo
construction (the CSV is a single snapshot with no time dimension): each
series is built as a monotonically degrading sequence of points that *ends*
at the battery's real CSV state_of_health value. This is not real telemetry.
"""
import json
import random
from datetime import datetime, timedelta, timezone

import numpy as np
import pandas as pd
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import hash_password
from app.db.base import Base
from app.db.session import SessionLocal, engine
from app.ml import features
from app.ml.labeling import soh_to_class
from app.ml.train import run_training
from app.ml.registry import save_model
from app.models.battery import Battery
from app.models.dataset import Dataset
from app.models.diagnostic import Diagnostic
from app.models.maintenance_item import MaintenanceItem
from app.models.measurement import BatteryMeasurement
from app.models.model_deployment import ModelDeployment
from app.models.notification import Notification
from app.models.training_run import TrainingRun
from app.models.user import User
from app.models.vehicle import Vehicle
from app.services import dataset_service
from app.services.prediction_service import run_diagnostic

SEED_RANDOM_STATE = 42

SCIENTIST_EMAIL = "scientist@evsoh.io"
TECH_EMAIL = "tech@evsoh.io"
OWNER_EMAIL = "owner@evsoh.io"

EXTRA_EV_USERS = [
    ("ev1@evsoh.io", "Maria Nguyen"),
    ("ev2@evsoh.io", "Daniel Osei"),
    ("ev3@evsoh.io", "Priya Patel"),
    ("ev4@evsoh.io", "Lucas Ferreira"),
]
EXTRA_TECHNICIANS = [
    ("tech2@evsoh.io", "Sam Okafor"),
    ("tech3@evsoh.io", "Yuki Tanaka"),
]


def _num(value):
    if value is None:
        return None
    try:
        if pd.isna(value):
            return None
    except (TypeError, ValueError):
        pass
    return float(value)


def _intval(value):
    n = _num(value)
    return int(n) if n is not None else None


def _strval(value):
    if value is None:
        return None
    try:
        if pd.isna(value):
            return None
    except (TypeError, ValueError):
        pass
    return str(value)


def get_or_create_user(db: Session, email: str, name: str, role: str) -> User:
    user = db.query(User).filter(User.email == email).first()
    if user is not None:
        return user
    user = User(email=email, name=name, role=role, password_hash=hash_password(settings.DEMO_PASSWORD))
    db.add(user)
    db.flush()
    return user


def seed_users(db: Session) -> dict:
    users = {
        "scientist": get_or_create_user(db, SCIENTIST_EMAIL, "Dr. Elena Vasquez", "data_scientist"),
        "tech": get_or_create_user(db, TECH_EMAIL, "Marcus Webb", "technician"),
        "owner": get_or_create_user(db, OWNER_EMAIL, "Jordan Lee", "ev_user"),
    }
    users["extra_ev_users"] = [
        get_or_create_user(db, email, name, "ev_user") for email, name in EXTRA_EV_USERS
    ]
    users["extra_technicians"] = [
        get_or_create_user(db, email, name, "technician") for email, name in EXTRA_TECHNICIANS
    ]
    db.commit()
    return users


def seed_dataset(db: Session, raw_df: pd.DataFrame, csv_bytes: bytes) -> Dataset:
    name = "ev_battery_failure_prediction_dataset.csv"
    existing = db.query(Dataset).filter(Dataset.filename == name).first()
    if existing is not None:
        return existing

    scientist = db.query(User).filter(User.email == SCIENTIST_EMAIL).first()
    dataset = dataset_service.create_dataset_record(
        db,
        name="EV Battery Failure Prediction Dataset",
        filename=name,
        content=csv_bytes,
        df=raw_df,
        uploaded_by_user_id=scientist.id if scientist else None,
    )
    return dataset


def select_seed_rows(df: pd.DataFrame) -> pd.DataFrame:
    labelled = df[df[settings.LABEL_SOURCE_COLUMN].notna()].copy()
    labelled[settings.DERIVED_LABEL_COLUMN] = labelled[settings.LABEL_SOURCE_COLUMN].map(soh_to_class)

    targets = {"GOOD": 24, "MONITOR": 24, "CRITICAL": 12}
    picked = []
    for cls, n in targets.items():
        bucket = labelled[labelled[settings.DERIVED_LABEL_COLUMN] == cls]
        n = min(n, len(bucket))
        picked.append(bucket.sample(n=n, random_state=SEED_RANDOM_STATE))
    rows = pd.concat(picked, axis=0).drop_duplicates(subset=["vehicle_id"])
    # health_class was only needed to stratify-sample above. Drop it now so no
    # downstream consumer (feature snapshot included) ever sees the derived
    # label riding along inside what should be a pure CSV row.
    rows = rows.drop(columns=[settings.DERIVED_LABEL_COLUMN])
    return rows.reset_index(drop=True)


def seed_vehicles_and_batteries(db: Session, rows: pd.DataFrame) -> list[Vehicle]:
    vehicles = []
    for _, row in rows.iterrows():
        vehicle_code = str(row["vehicle_id"])
        existing = db.query(Vehicle).filter(Vehicle.vehicle_code == vehicle_code).first()
        if existing is not None:
            vehicles.append(existing)
            continue

        serial = str(row["battery_serial"])
        snapshot = features.feature_dict_from_row(pd.DataFrame([row]))

        battery = Battery(
            serial=serial,
            manufacturer=_strval(row.get("battery_manufacturer")),
            chemistry=_strval(row.get("battery_chemistry")),
            capacity_kwh=_num(row.get("battery_capacity_kwh")),
            cycle_count=_num(row.get("cycle_count")),
            current_soh=_num(row.get(settings.LABEL_SOURCE_COLUMN)),
            feature_snapshot_json=json.dumps(snapshot),
        )
        db.add(battery)
        db.flush()

        vehicle = Vehicle(
            vehicle_code=vehicle_code,
            brand=_strval(row.get("vehicle_brand")),
            model=_strval(row.get("vehicle_model")),
            vehicle_type=_strval(row.get("vehicle_type")),
            manufacturing_year=_intval(row.get("manufacturing_year")),
            drive_type=_strval(row.get("drive_type")),
            odometer_km=_num(row.get("odometer_km")),
            fleet_or_private=_strval(row.get("fleet_or_private")),
            battery_id=battery.id,
            owner_user_id=None,
        )
        db.add(vehicle)
        db.flush()
        vehicles.append(vehicle)

    db.commit()
    return vehicles


def assign_owners(db: Session, vehicles: list[Vehicle], users: dict) -> None:
    def battery_of(v: Vehicle) -> Battery:
        return db.get(Battery, v.battery_id)

    already_owned = {v.id for v in vehicles if v.owner_user_id is not None}
    if already_owned:
        return  # idempotent: ownership already assigned on a previous run

    critical_vehicles = [v for v in vehicles if battery_of(v).current_soh is not None and soh_to_class(battery_of(v).current_soh) == "CRITICAL"]
    owner_vehicle = critical_vehicles[0] if critical_vehicles else vehicles[0]
    owner_vehicle.owner_user_id = users["owner"].id

    remaining = [v for v in vehicles if v.id != owner_vehicle.id]
    for ev_user, vehicle in zip(users["extra_ev_users"], remaining):
        vehicle.owner_user_id = ev_user.id

    db.commit()


def _degrading_series(end_value: float, points: int, rng: random.Random) -> list[float]:
    start_bump = rng.uniform(3.0, 9.0)
    start_value = min(100.0, end_value + start_bump)
    raw = np.linspace(start_value, end_value, points)
    noise = np.array([rng.uniform(-0.15, 0.15) for _ in range(points)])
    series = raw + noise
    # Enforce monotonic non-increase and clamp the final point to the real value.
    for i in range(1, points):
        if series[i] > series[i - 1]:
            series[i] = series[i - 1]
    series[-1] = end_value
    return [round(float(v), 2) for v in series]


def seed_measurements(db: Session, vehicles: list[Vehicle], row_by_serial: dict) -> None:
    for vehicle in vehicles:
        battery = db.get(Battery, vehicle.battery_id)
        has_measurements = (
            db.query(BatteryMeasurement).filter(BatteryMeasurement.battery_id == battery.id).first()
        )
        if has_measurements is not None:
            continue

        row = row_by_serial.get(battery.serial)
        if row is None or battery.current_soh is None:
            continue

        rng = random.Random(f"{battery.serial}-measurements")
        n_points = settings.SEED_MEASUREMENTS_PER_BATTERY
        soh_series = _degrading_series(battery.current_soh, n_points, rng)

        now = datetime.now(timezone.utc)
        base_cycle = _num(row.get("cycle_count")) or 0.0
        base_resistance = _num(row.get("internal_resistance"))
        base_soc = _num(row.get("state_of_charge"))
        base_voltage = _num(row.get("cell_voltage_avg"))
        base_temp_avg = _num(row.get("cell_temperature_avg"))
        base_temp_max = _num(row.get("cell_temperature_max"))
        base_efficiency = _num(row.get("charge_efficiency"))

        for i, soh_value in enumerate(soh_series):
            days_ago = (n_points - 1 - i) * 30
            recorded_at = now - timedelta(days=days_ago)
            ratio = soh_value / battery.current_soh if battery.current_soh else 1.0

            measurement = BatteryMeasurement(
                battery_id=battery.id,
                recorded_at=recorded_at,
                soh=soh_value,
                state_of_charge=round(base_soc + rng.uniform(-3, 3), 2) if base_soc is not None else None,
                internal_resistance=(
                    round(base_resistance / max(ratio, 0.5), 4) if base_resistance is not None else None
                ),
                cell_voltage_avg=(
                    round(base_voltage + rng.uniform(-0.02, 0.02), 4) if base_voltage is not None else None
                ),
                cell_temperature_avg=(
                    round(base_temp_avg + rng.uniform(-1.5, 1.5), 2) if base_temp_avg is not None else None
                ),
                cell_temperature_max=(
                    round(base_temp_max + rng.uniform(-1.5, 1.5), 2) if base_temp_max is not None else None
                ),
                charge_efficiency=(
                    round(base_efficiency + rng.uniform(-1, 1), 2) if base_efficiency is not None else None
                ),
                cycle_count=round(base_cycle * ratio, 0) if base_cycle else None,
            )
            db.add(measurement)
    db.commit()


def seed_training_and_deployment(db: Session, dataset: Dataset, scientist: User) -> TrainingRun:
    existing = db.query(TrainingRun).filter(TrainingRun.dataset_id == dataset.id).first()
    if existing is not None:
        return existing

    df = dataset_service.load_dataset_dataframe(dataset)
    params = settings.DEFAULT_PARAMS["random_forest"]
    started_at = datetime.now(timezone.utc)

    result = run_training(df, "random_forest", params, settings.DEFAULT_TEST_SIZE)

    run = TrainingRun(
        dataset_id=dataset.id,
        algorithm="random_forest",
        params_json=json.dumps(params),
        test_size=settings.DEFAULT_TEST_SIZE,
        status="completed",
        error=None,
        started_at=started_at,
        completed_at=datetime.now(timezone.utc),
        duration_seconds=result.duration_seconds,
        dropped_missing_label=result.dropped_missing_label,
        train_rows=result.train_rows,
        test_rows=result.test_rows,
        metrics_json=json.dumps(result.metrics),
        confusion_matrix_json=json.dumps(result.confusion_matrix),
        feature_importance_json=json.dumps(result.feature_importance),
        supports_probability=result.supports_probability,
        created_by_user_id=scientist.id,
    )
    db.add(run)
    db.flush()

    run.model_path = save_model(run.id, result.pipeline)
    db.commit()
    db.refresh(run)

    deployment = ModelDeployment(run_id=run.id, deployed_at=datetime.now(timezone.utc), active=True)
    db.add(deployment)
    db.commit()

    return run


def seed_diagnostics(db: Session, vehicles: list[Vehicle], users: dict) -> None:
    existing = db.query(Diagnostic).first()
    if existing is not None:
        return

    technicians = [users["tech"], *users["extra_technicians"]]
    rng = random.Random("diagnostics-seed")
    sample_size = min(settings.SEED_DIAGNOSTICS_COUNT, len(vehicles))
    chosen = rng.sample(vehicles, k=sample_size)

    now = datetime.now(timezone.utc)
    for i, vehicle in enumerate(chosen):
        battery = db.get(Battery, vehicle.battery_id)
        technician = technicians[i % len(technicians)]
        diagnostic = run_diagnostic(db, vehicle, battery, technician, notes=None)
        diagnostic.created_at = now - timedelta(days=i, hours=rng.randint(0, 23))
        db.commit()


def seed_notifications(db: Session, users: dict) -> None:
    all_users = [
        users["scientist"],
        users["tech"],
        users["owner"],
        *users["extra_ev_users"],
        *users["extra_technicians"],
    ]
    existing = db.query(Notification).first()
    if existing is not None:
        return

    now = datetime.now(timezone.utc)
    for user in all_users:
        notification = Notification(
            user_id=user.id,
            type="system",
            severity="info",
            title="Welcome to EV Battery SoH Classification",
            body="Your account is set up. Explore your dashboard to get started.",
            created_at=now - timedelta(days=1),
            read_at=None,
        )
        db.add(notification)
    db.commit()


def seed_maintenance(db: Session, vehicles: list[Vehicle], users: dict) -> None:
    existing = db.query(MaintenanceItem).first()
    if existing is not None:
        return

    owned_vehicles = [v for v in vehicles if v.owner_user_id is not None]
    now = datetime.now(timezone.utc)
    for vehicle in owned_vehicles:
        battery = db.get(Battery, vehicle.battery_id)
        health_class = soh_to_class(battery.current_soh) if battery.current_soh is not None else "GOOD"

        items = [
            MaintenanceItem(
                user_id=vehicle.owner_user_id,
                title="Annual firmware update",
                description="Check for and install the latest battery management firmware.",
                severity="info",
                due_at=now + timedelta(days=60),
                completed=False,
            )
        ]
        if health_class == "MONITOR":
            items.append(
                MaintenanceItem(
                    user_id=vehicle.owner_user_id,
                    title="Schedule a capacity inspection",
                    description="Battery degradation detected. Book a service appointment soon.",
                    severity="warning",
                    due_at=now + timedelta(days=14),
                    completed=False,
                )
            )
        elif health_class == "CRITICAL":
            items.append(
                MaintenanceItem(
                    user_id=vehicle.owner_user_id,
                    title="Immediate battery inspection required",
                    description="Battery health is below the safe threshold. Contact a service center now.",
                    severity="critical",
                    due_at=now + timedelta(days=3),
                    completed=False,
                )
            )
        for item in items:
            db.add(item)
    db.commit()


def seed() -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        already_seeded = db.query(User).filter(User.email == SCIENTIST_EMAIL).first() is not None
        if already_seeded:
            print("Seed data already present. Skipping (idempotent).")
            return

        print("Loading CSV...")
        csv_bytes = settings.SOURCE_CSV_PATH.read_bytes()
        raw_df = pd.read_csv(settings.SOURCE_CSV_PATH)

        print("Seeding users...")
        users = seed_users(db)

        print("Seeding dataset...")
        dataset = seed_dataset(db, raw_df, csv_bytes)

        print("Selecting vehicles/batteries from real CSV rows...")
        rows = select_seed_rows(raw_df)
        row_by_serial = {str(r["battery_serial"]): r for _, r in rows.iterrows()}

        print(f"Seeding {len(rows)} vehicles + batteries...")
        vehicles = seed_vehicles_and_batteries(db, rows)

        print("Assigning EV user ownership...")
        assign_owners(db, vehicles, users)

        print("Seeding historical measurements...")
        seed_measurements(db, vehicles, row_by_serial)

        print("Training and deploying a real model (random_forest)...")
        run = seed_training_and_deployment(db, dataset, users["scientist"])
        print(f"  trained run id={run.id} accuracy={json.loads(run.metrics_json)['accuracy']:.4f}")

        print("Seeding diagnostics (real predictions from the deployed model)...")
        seed_diagnostics(db, vehicles, users)

        print("Seeding notifications...")
        seed_notifications(db, users)

        print("Seeding maintenance items...")
        seed_maintenance(db, vehicles, users)

        print("Seed complete.")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
