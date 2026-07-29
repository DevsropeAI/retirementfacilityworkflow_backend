from pydantic import BaseModel
from typing import Optional
from datetime import date, datetime

class AgreementCreate(BaseModel):
    lead_id: int
    application_id: Optional[int] = None
    facility: str
    room_number: Optional[str] = None
    move_in_date: date
    monthly_fee: float
    security_deposit: Optional[float] = None
    terms_conditions: Optional[str] = None

class AgreementUpdate(BaseModel):
    facility: Optional[str] = None
    room_number: Optional[str] = None
    move_in_date: Optional[date] = None
    monthly_fee: Optional[float] = None
    security_deposit: Optional[float] = None
    terms_conditions: Optional[str] = None
    status: Optional[str] = None

class AgreementResponse(BaseModel):
    id: int
    lead_id: int
    application_id: Optional[int]
    agreement_number: str
    facility: str
    room_number: Optional[str]
    move_in_date: date
    monthly_fee: float
    security_deposit: Optional[float]
    terms_conditions: Optional[str]
    status: str
    token: Optional[str]
    signed_at: Optional[datetime]
    signed_pdf_path: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]
    sent_at: Optional[datetime]
    
    # Lead info
    lead_name: Optional[str] = None
    lead_email: Optional[str] = None
    lead_phone: Optional[str] = None
    
    class Config:
        from_attributes = True

class AgreementSignRequest(BaseModel):
    signature_image: str  # Base64 image data