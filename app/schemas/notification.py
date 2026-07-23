from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class NotificationCreate(BaseModel):
    staff_id: int
    title: str
    message: str
    type: str
    link: Optional[str] = None

class NotificationResponse(BaseModel):
    id: int
    staff_id: int
    title: str
    message: str
    type: str
    link: Optional[str]
    is_read: int
    created_at: datetime
    
    class Config:
        from_attributes = True