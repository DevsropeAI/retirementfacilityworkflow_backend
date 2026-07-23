from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class ConsultationCreate(BaseModel):
    lead_id: int
    consultation_type: str  # phone, zoom, facility_tour
    scheduled_date: str  # ISO date string
    scheduled_time: str  # "10:00 AM"
    duration: Optional[int] = 60
    notes: Optional[str] = None
    meeting_link: Optional[str] = None
    meeting_id: Optional[str] = None

class ConsultationUpdate(BaseModel):
    consultation_type: Optional[str] = None
    scheduled_date: Optional[str] = None
    scheduled_time: Optional[str] = None
    duration: Optional[int] = None
    notes: Optional[str] = None
    status: Optional[str] = None  # scheduled, completed, cancelled, no_show
    meeting_link: Optional[str] = None
    meeting_id: Optional[str] = None

class ConsultationResponse(BaseModel):
    id: int
    lead_id: int
    consultation_type: str
    scheduled_date: datetime
    scheduled_time: str
    duration: int
    notes: Optional[str]
    status: str
    meeting_link: Optional[str]
    meeting_id: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]
    
    # Lead info (for display)
    lead_name: Optional[str] = None
    lead_email: Optional[str] = None
    lead_phone: Optional[str] = None
    
    class Config:
        from_attributes = True