"""All notification creation goes through this module (ARCHITECTURE.md 4.9).

This is the seam where a real push transport (FCM/APNs/web-push) can later be
added: swap the body of `create_notification` to also call that transport,
without touching any call site that creates a notification today.
"""
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.notification import Notification


def create_notification(
    db: Session, user_id: int, type_: str, severity: str, title: str, body: str
) -> Notification:
    notification = Notification(
        user_id=user_id,
        type=type_,
        severity=severity,
        title=title,
        body=body,
        created_at=datetime.now(timezone.utc),
        read_at=None,
    )
    db.add(notification)
    db.commit()
    db.refresh(notification)
    # Seam for a future real push transport (FCM/APNs/web-push):
    # push_transport.send(user_id, title, body)
    return notification


def list_notifications(db: Session, user_id: int) -> list[Notification]:
    return (
        db.query(Notification)
        .filter(Notification.user_id == user_id)
        .order_by(Notification.created_at.desc())
        .all()
    )


def mark_read(db: Session, notification_id: int, user_id: int) -> Notification | None:
    notification = (
        db.query(Notification)
        .filter(Notification.id == notification_id, Notification.user_id == user_id)
        .first()
    )
    if notification is None:
        return None
    if notification.read_at is None:
        notification.read_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(notification)
    return notification


def mark_all_read(db: Session, user_id: int) -> None:
    now = datetime.now(timezone.utc)
    (
        db.query(Notification)
        .filter(Notification.user_id == user_id, Notification.read_at.is_(None))
        .update({"read_at": now})
    )
    db.commit()
