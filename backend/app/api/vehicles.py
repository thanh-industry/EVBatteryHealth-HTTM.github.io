from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.core.security import require_role
from app.db.session import get_db
from app.models.battery import Battery
from app.models.measurement import BatteryMeasurement
from app.models.user import User
from app.models.vehicle import Vehicle
from app.schemas.vehicles import Measurement, Vehicle as VehicleSchema, VehicleDetail
from app.services import vehicle_service

router = APIRouter(tags=["vehicles"])

_require_viewer = require_role("technician", "ev_user")


@router.get("/api/vehicles", response_model=list[VehicleSchema])
def list_vehicles(
    q: str | None = Query(default=None),
    db: Session = Depends(get_db),
    _user: User = Depends(_require_viewer),
) -> list[VehicleSchema]:
    query = db.query(Vehicle).join(Battery, Vehicle.battery_id == Battery.id)
    if q:
        pattern = f"%{q.lower()}%"
        query = query.filter(
            or_(
                Vehicle.vehicle_code.ilike(pattern),
                Vehicle.brand.ilike(pattern),
                Vehicle.model.ilike(pattern),
                Battery.serial.ilike(pattern),
            )
        )
    vehicles = query.order_by(Vehicle.vehicle_code).all()
    return [
        VehicleSchema(**vehicle_service.vehicle_to_schema(v, v.battery)) for v in vehicles
    ]


@router.get("/api/vehicles/{vehicle_code}", response_model=VehicleDetail)
def get_vehicle(
    vehicle_code: str, db: Session = Depends(get_db), _user: User = Depends(_require_viewer)
) -> VehicleDetail:
    vehicle = vehicle_service.find_vehicle_by_code(db, vehicle_code)
    if vehicle is None:
        raise HTTPException(status_code=404, detail=f"Vehicle '{vehicle_code}' not found.")
    return VehicleDetail(**vehicle_service.vehicle_detail_to_schema(db, vehicle, vehicle.battery))


@router.get("/api/batteries/lookup", response_model=VehicleDetail)
def lookup_battery(
    code: str = Query(...), db: Session = Depends(get_db), _user: User = Depends(_require_viewer)
) -> VehicleDetail:
    vehicle = vehicle_service.find_by_vehicle_or_battery_code(db, code)
    if vehicle is None:
        raise HTTPException(status_code=404, detail=f"No vehicle or battery matching '{code}' found.")
    return VehicleDetail(**vehicle_service.vehicle_detail_to_schema(db, vehicle, vehicle.battery))


@router.get("/api/batteries/{serial}/measurements", response_model=list[Measurement])
def get_measurements(
    serial: str, db: Session = Depends(get_db), _user: User = Depends(_require_viewer)
) -> list[Measurement]:
    battery = db.query(Battery).filter(Battery.serial.ilike(serial)).first()
    if battery is None:
        raise HTTPException(status_code=404, detail=f"Battery '{serial}' not found.")
    measurements = (
        db.query(BatteryMeasurement)
        .filter(BatteryMeasurement.battery_id == battery.id)
        .order_by(BatteryMeasurement.recorded_at.asc())
        .all()
    )
    return [Measurement(**vehicle_service.measurement_to_schema(m)) for m in measurements]
