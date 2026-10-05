"""Runs the active deployed model against a battery's latest measurement and
persists a Diagnostic (ARCHITECTURE.md 4.7).

Feature construction: each seeded Battery carries a `feature_snapshot_json` -
the original CSV row's feature columns (leakage blocklist already removed by
ml.features.build_feature_frame at seed time). At diagnosis time this base
snapshot is overlaid with the fields that genuinely come from the battery's
*latest measurement* (state_of_charge, internal_resistance, cell voltage /
temperature, charge_efficiency, cycle_count) so the prediction is run against
current telemetry, not a stale snapshot. The remaining columns (vehicle
specs, driving/charging behaviour, environment) have no time series in this
dataset - the CSV is a single snapshot - so they are held at their sampled
value.

IMPORTANT: feature_snapshot_json is CSV-derived demo data, not live sensor
telemetry. It is a one-time snapshot of a real CSV row taken at seed time
(leakage blocklist and the derived label already stripped by
ml.features.build_feature_frame), used only so this demo has a plausible
feature vector to diagnose against. Nobody should mistake it for a live BMS
feed - that is the same documented demo construction as the measurement
history itself (ARCHITECTURE.md 6).
"""
import json
from datetime import datetime, timezone

import pandas as pd
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.recommendations import get_recommendation
from app.ml import registry
from app.ml.registry import ModelLoadError
from app.models.battery import Battery
from app.models.diagnostic import Diagnostic
from app.models.measurement import BatteryMeasurement
from app.models.model_deployment import ModelDeployment
from app.models.training_run import TrainingRun
from app.models.user import User
from app.models.vehicle import Vehicle
from app.services import notification_service

_MEASUREMENT_OVERLAY_FIELDS = [
    "state_of_charge",
    "internal_resistance",
    "cell_voltage_avg",
    "cell_temperature_avg",
    "cell_temperature_max",
    "charge_efficiency",
    "cycle_count",
]


def get_active_deployment(db: Session) -> ModelDeployment | None:
    return db.query(ModelDeployment).filter(ModelDeployment.active.is_(True)).first()


def build_feature_row(battery: Battery, measurement: BatteryMeasurement) -> dict:
    snapshot = json.loads(battery.feature_snapshot_json) if battery.feature_snapshot_json else {}
    for field in _MEASUREMENT_OVERLAY_FIELDS:
        value = getattr(measurement, field, None)
        if value is not None:
            snapshot[field] = value
    return snapshot


def _class_probabilities(pipeline, proba_row) -> list[dict]:
    estimator = pipeline.named_steps["estimator"]
    class_to_proba = dict(zip(estimator.classes_, proba_row))
    return [
        {"class": cls, "probability": float(class_to_proba.get(cls, 0.0))}
        for cls in settings.SOH_CLASSES
    ]


def _maybe_notify(db: Session, vehicle: Vehicle, predicted_class: str) -> None:
    if vehicle.owner_user_id is None:
        return
    if predicted_class == "CRITICAL":
        notification_service.create_notification(
            db,
            user_id=vehicle.owner_user_id,
            type_="critical_health",
            severity="critical",
            title="Battery health is critical",
            body=f"Vehicle {vehicle.vehicle_code} battery was diagnosed as CRITICAL. Immediate inspection is recommended.",
        )
    elif predicted_class == "MONITOR":
        notification_service.create_notification(
            db,
            user_id=vehicle.owner_user_id,
            type_="degradation",
            severity="warning",
            title="Battery degradation detected",
            body=f"Vehicle {vehicle.vehicle_code} battery now needs monitoring. Schedule an inspection soon.",
        )


def run_diagnostic(
    db: Session,
    vehicle: Vehicle,
    battery: Battery,
    technician: User | None,
    notes: str | None,
) -> Diagnostic:
    deployment = get_active_deployment(db)
    if deployment is None:
        raise HTTPException(
            status_code=409, detail="No model is currently deployed. Deploy a trained model first."
        )

    run = db.get(TrainingRun, deployment.run_id)
    if run is None:
        raise HTTPException(
            status_code=409, detail="No model is currently deployed. Deploy a trained model first."
        )

    try:
        pipeline = registry.load_model(run.model_path)
    except ModelLoadError as exc:
        raise HTTPException(status_code=409, detail=f"Deployed model is unavailable: {exc}")

    measurement = (
        db.query(BatteryMeasurement)
        .filter(BatteryMeasurement.battery_id == battery.id)
        .order_by(BatteryMeasurement.recorded_at.desc())
        .first()
    )
    if measurement is None:
        raise HTTPException(status_code=409, detail="No measurement data available for this battery.")

    feature_row = build_feature_row(battery, measurement)
    X = pd.DataFrame([feature_row])

    predicted_class = str(pipeline.predict(X)[0])

    confidence: float | None = None
    class_probabilities: list[dict] | None = None
    if run.supports_probability and hasattr(pipeline, "predict_proba"):
        proba_row = pipeline.predict_proba(X)[0]
        class_probabilities = _class_probabilities(pipeline, proba_row)
        confidence = float(max(proba_row))

    diagnostic = Diagnostic(
        vehicle_id=vehicle.id,
        battery_id=battery.id,
        run_id=run.id,
        created_at=datetime.now(timezone.utc),
        soh=measurement.soh,
        predicted_class=predicted_class,
        confidence=confidence,
        class_probabilities_json=json.dumps(class_probabilities) if class_probabilities else None,
        model_version=f"v{run.id}",
        model_algorithm=run.algorithm,
        technician_user_id=technician.id if technician else None,
        recommendation=get_recommendation(predicted_class),
        notes=notes,
    )
    db.add(diagnostic)
    db.commit()
    db.refresh(diagnostic)

    _maybe_notify(db, vehicle, predicted_class)

    return diagnostic


def diagnostic_to_schema(db: Session, diagnostic: Diagnostic) -> dict:
    vehicle = db.get(Vehicle, diagnostic.vehicle_id)
    battery = db.get(Battery, diagnostic.battery_id)
    technician = db.get(User, diagnostic.technician_user_id) if diagnostic.technician_user_id else None
    return {
        "id": diagnostic.id,
        "vehicle_code": vehicle.vehicle_code if vehicle else "",
        "battery_serial": battery.serial if battery else "",
        "created_at": diagnostic.created_at,
        "soh": diagnostic.soh,
        "predicted_class": diagnostic.predicted_class,
        "confidence": diagnostic.confidence,
        "class_probabilities": (
            json.loads(diagnostic.class_probabilities_json)
            if diagnostic.class_probabilities_json
            else None
        ),
        "model_version": diagnostic.model_version,
        "model_algorithm": diagnostic.model_algorithm,
        "technician_name": technician.name if technician else None,
        "recommendation": diagnostic.recommendation,
        "notes": diagnostic.notes,
    }
