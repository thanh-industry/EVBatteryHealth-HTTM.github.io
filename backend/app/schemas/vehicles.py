from datetime import datetime

from pydantic import BaseModel

from app.schemas.common import HealthClass


class Vehicle(BaseModel):
    vehicle_code: str
    brand: str | None
    model: str | None
    vehicle_type: str | None
    manufacturing_year: int | None
    drive_type: str | None
    odometer_km: float | None
    fleet_or_private: str | None
    battery_serial: str
    current_soh: float | None
    health_class: HealthClass | None


class Battery(BaseModel):
    serial: str
    manufacturer: str | None
    chemistry: str | None
    capacity_kwh: float | None
    cycle_count: float | None
    current_soh: float | None
    health_class: HealthClass | None


class Measurement(BaseModel):
    recorded_at: datetime
    soh: float
    state_of_charge: float | None
    internal_resistance: float | None
    cell_voltage_avg: float | None
    cell_temperature_avg: float | None
    cell_temperature_max: float | None
    charge_efficiency: float | None
    cycle_count: float | None


class VehicleDetail(BaseModel):
    vehicle: Vehicle
    battery: Battery
    latest_measurement: Measurement | None
    measurement_count: int
    last_diagnostic_at: datetime | None
