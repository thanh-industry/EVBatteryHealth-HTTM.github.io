from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.recommendations import get_recommendation
from app.core.security import require_role
from app.db.session import get_db
from app.models.maintenance_item import MaintenanceItem as MaintenanceItemModel
from app.models.user import User
from app.models.vehicle import Vehicle
from app.schemas.me import MaintenanceItem, UserBatteryOverview
from app.schemas.vehicles import Measurement
from app.services import vehicle_service

router = APIRouter(prefix="/api/me", tags=["me"])

_require_ev_user = require_role("ev_user")


def _get_owned_vehicle(db: Session, user: User) -> Vehicle:
    vehicle = db.query(Vehicle).filter(Vehicle.owner_user_id == user.id).first()
    if vehicle is None:
        raise HTTPException(status_code=404, detail="No vehicle is associated with this account.")
    return vehicle


@router.get("/battery", response_model=UserBatteryOverview)
def get_my_battery(
    db: Session = Depends(get_db), user: User = Depends(_require_ev_user)
) -> UserBatteryOverview:
    vehicle = _get_owned_vehicle(db, user)
    battery = vehicle.battery
    measurements = vehicle_service.get_measurement_history(db, battery.id)
    latest = measurements[-1] if measurements else None
    health_class = vehicle_service.health_class_for(battery.current_soh)

    return UserBatteryOverview(
        vehicle=vehicle_service.vehicle_to_schema(vehicle, battery),
        battery=vehicle_service.battery_to_schema(battery),
        current_soh=battery.current_soh,
        health_class=health_class,
        last_checked_at=latest.recorded_at if latest else None,
        soh_change_30d=vehicle_service.compute_soh_change_30d(measurements),
        recommendation=get_recommendation(health_class) if health_class else "No data available yet.",
        history=[vehicle_service.measurement_to_schema(m) for m in measurements],
    )


@router.get("/battery/history", response_model=list[Measurement])
def get_my_battery_history(
    db: Session = Depends(get_db), user: User = Depends(_require_ev_user)
) -> list[Measurement]:
    vehicle = _get_owned_vehicle(db, user)
    measurements = vehicle_service.get_measurement_history(db, vehicle.battery.id)
    return [Measurement(**vehicle_service.measurement_to_schema(m)) for m in measurements]


@router.get("/maintenance", response_model=list[MaintenanceItem])
def get_my_maintenance(
    db: Session = Depends(get_db), user: User = Depends(_require_ev_user)
) -> list[MaintenanceItem]:
    items = (
        db.query(MaintenanceItemModel)
        .filter(MaintenanceItemModel.user_id == user.id)
        .order_by(MaintenanceItemModel.due_at.asc())
        .all()
    )
    return [
        MaintenanceItem(
            id=i.id,
            title=i.title,
            description=i.description,
            severity=i.severity,
            due_at=i.due_at,
            completed=i.completed,
        )
        for i in items
    ]
