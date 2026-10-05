"""Shared vehicle/battery lookup and serialization helpers.

Used by the vehicles, diagnostics, and me routers so lookup-by-human-code
logic (case-insensitive, 404-clean) lives in exactly one place.
"""
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.ml.labeling import soh_to_class
from app.models.battery import Battery
from app.models.diagnostic import Diagnostic
from app.models.measurement import BatteryMeasurement
from app.models.vehicle import Vehicle


def health_class_for(soh: float | None) -> str | None:
    if soh is None:
        return None
    return soh_to_class(soh)


def find_vehicle_by_code(db: Session, vehicle_code: str) -> Vehicle | None:
    return db.query(Vehicle).filter(func.lower(Vehicle.vehicle_code) == vehicle_code.lower()).first()


def find_by_vehicle_or_battery_code(db: Session, code: str) -> Vehicle | None:
    code_lower = code.lower()
    vehicle = db.query(Vehicle).filter(func.lower(Vehicle.vehicle_code) == code_lower).first()
    if vehicle is not None:
        return vehicle
    battery = db.query(Battery).filter(func.lower(Battery.serial) == code_lower).first()
    if battery is None:
        return None
    return db.query(Vehicle).filter(Vehicle.battery_id == battery.id).first()


def get_latest_measurement(db: Session, battery_id: int) -> BatteryMeasurement | None:
    return (
        db.query(BatteryMeasurement)
        .filter(BatteryMeasurement.battery_id == battery_id)
        .order_by(BatteryMeasurement.recorded_at.desc())
        .first()
    )


def get_measurement_count(db: Session, battery_id: int) -> int:
    return db.query(BatteryMeasurement).filter(BatteryMeasurement.battery_id == battery_id).count()


def get_measurement_history(db: Session, battery_id: int) -> list[BatteryMeasurement]:
    return (
        db.query(BatteryMeasurement)
        .filter(BatteryMeasurement.battery_id == battery_id)
        .order_by(BatteryMeasurement.recorded_at.asc())
        .all()
    )


def compute_soh_change_30d(measurements: list[BatteryMeasurement]) -> float | None:
    """Percentage-point change in SoH over the last 30 days of history.
    Negative = degrading. None if there is not enough history to compare.
    """
    if len(measurements) < 2:
        return None
    from datetime import timedelta

    latest = measurements[-1]
    target = latest.recorded_at - timedelta(days=30)
    candidates = [m for m in measurements if m.recorded_at <= target]
    baseline = candidates[-1] if candidates else measurements[0]
    if baseline is latest:
        return None
    return round(latest.soh - baseline.soh, 4)


def get_last_diagnostic_at(db: Session, vehicle_id: int):
    diagnostic = (
        db.query(Diagnostic)
        .filter(Diagnostic.vehicle_id == vehicle_id)
        .order_by(Diagnostic.created_at.desc())
        .first()
    )
    return diagnostic.created_at if diagnostic else None


def vehicle_to_schema(vehicle: Vehicle, battery: Battery) -> dict:
    return {
        "vehicle_code": vehicle.vehicle_code,
        "brand": vehicle.brand,
        "model": vehicle.model,
        "vehicle_type": vehicle.vehicle_type,
        "manufacturing_year": vehicle.manufacturing_year,
        "drive_type": vehicle.drive_type,
        "odometer_km": vehicle.odometer_km,
        "fleet_or_private": vehicle.fleet_or_private,
        "battery_serial": battery.serial,
        "current_soh": battery.current_soh,
        "health_class": health_class_for(battery.current_soh),
    }


def battery_to_schema(battery: Battery) -> dict:
    return {
        "serial": battery.serial,
        "manufacturer": battery.manufacturer,
        "chemistry": battery.chemistry,
        "capacity_kwh": battery.capacity_kwh,
        "cycle_count": battery.cycle_count,
        "current_soh": battery.current_soh,
        "health_class": health_class_for(battery.current_soh),
    }


def measurement_to_schema(measurement: BatteryMeasurement) -> dict:
    return {
        "recorded_at": measurement.recorded_at,
        "soh": measurement.soh,
        "state_of_charge": measurement.state_of_charge,
        "internal_resistance": measurement.internal_resistance,
        "cell_voltage_avg": measurement.cell_voltage_avg,
        "cell_temperature_avg": measurement.cell_temperature_avg,
        "cell_temperature_max": measurement.cell_temperature_max,
        "charge_efficiency": measurement.charge_efficiency,
        "cycle_count": measurement.cycle_count,
    }


def vehicle_detail_to_schema(db: Session, vehicle: Vehicle, battery: Battery) -> dict:
    latest = get_latest_measurement(db, battery.id)
    return {
        "vehicle": vehicle_to_schema(vehicle, battery),
        "battery": battery_to_schema(battery),
        "latest_measurement": measurement_to_schema(latest) if latest else None,
        "measurement_count": get_measurement_count(db, battery.id),
        "last_diagnostic_at": get_last_diagnostic_at(db, vehicle.id),
    }
