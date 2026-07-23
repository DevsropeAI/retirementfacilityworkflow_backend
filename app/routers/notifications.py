from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.core.security import decode_token
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.services.notification_service import (
    get_unread_count, get_notifications, mark_as_read, mark_all_as_read
)
from app.schemas.notification import NotificationResponse

router = APIRouter()
security = HTTPBearer()

def get_current_staff(token: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)):
    payload = decode_token(token.credentials)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    return payload.get("id")

@router.get("/unread-count")
def unread_count(
    db: Session = Depends(get_db),
    staff_id: int = Depends(get_current_staff)
):
    return {"count": get_unread_count(db, staff_id)}

@router.get("/", response_model=List[NotificationResponse])
def get_notifications_list(
    db: Session = Depends(get_db),
    staff_id: int = Depends(get_current_staff)
):
    return get_notifications(db, staff_id)

@router.put("/{notification_id}/read")
def mark_read(
    notification_id: int,
    db: Session = Depends(get_db),
    staff_id: int = Depends(get_current_staff)
):
    notification = mark_as_read(db, notification_id, staff_id)
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")
    return {"message": "Marked as read"}

@router.put("/read-all")
def mark_all_read(
    db: Session = Depends(get_db),
    staff_id: int = Depends(get_current_staff)
):
    mark_all_as_read(db, staff_id)
    return {"message": "All notifications marked as read"}