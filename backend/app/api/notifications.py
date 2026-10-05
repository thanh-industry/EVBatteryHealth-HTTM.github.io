from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.notifications import Notification as NotificationSchema
from app.services import notification_service

router = APIRouter(prefix="/api/notifications", tags=["notifications"])


@router.get("", response_model=list[NotificationSchema])
def list_notifications(
    db: Session = Depends(get_db), user: User = Depends(get_current_user)
) -> list[NotificationSchema]:
    notifications = notification_service.list_notifications(db, user.id)
    return [NotificationSchema.model_validate(n) for n in notifications]


@router.post("/{notification_id}/read", response_model=NotificationSchema)
def mark_notification_read(
    notification_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> NotificationSchema:
    notification = notification_service.mark_read(db, notification_id, user.id)
    if notification is None:
        raise HTTPException(status_code=404, detail=f"Notification {notification_id} not found.")
    return NotificationSchema.model_validate(notification)


@router.post("/read-all", status_code=204)
def mark_all_notifications_read(
    db: Session = Depends(get_db), user: User = Depends(get_current_user)
) -> None:
    notification_service.mark_all_read(db, user.id)
    return None
