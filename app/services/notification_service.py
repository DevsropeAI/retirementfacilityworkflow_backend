from app.models.db_models import Notification
from sqlalchemy.orm import Session
from datetime import datetime

def create_notification(db: Session, staff_id: int, title: str, message: str, type: str, link: str = None):
    """Create a new notification for a staff member"""
    notification = Notification(
        staff_id=staff_id,
        title=title,
        message=message,
        type=type,
        link=link,
        is_read=0
    )
    db.add(notification)
    db.commit()
    db.refresh(notification)
    return notification

def get_unread_count(db: Session, staff_id: int):
    """Get count of unread notifications for a staff member"""
    return db.query(Notification).filter(
        Notification.staff_id == staff_id,
        Notification.is_read == 0
    ).count()

def get_notifications(db: Session, staff_id: int, limit: int = 20):
    """Get recent notifications for a staff member"""
    return db.query(Notification).filter(
        Notification.staff_id == staff_id
    ).order_by(Notification.created_at.desc()).limit(limit).all()

def mark_as_read(db: Session, notification_id: int, staff_id: int):
    """Mark a notification as read"""
    notification = db.query(Notification).filter(
        Notification.id == notification_id,
        Notification.staff_id == staff_id
    ).first()
    if notification:
        notification.is_read = 1
        db.commit()
        db.refresh(notification)
        return notification
    return None

def mark_all_as_read(db: Session, staff_id: int):
    """Mark all notifications as read for a staff member"""
    db.query(Notification).filter(
        Notification.staff_id == staff_id,
        Notification.is_read == 0
    ).update({"is_read": 1})
    db.commit()