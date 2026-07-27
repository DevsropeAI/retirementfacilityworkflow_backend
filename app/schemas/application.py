from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class ApplicationCreate(BaseModel):
    lead_id: int
    full_name: str
    email: str
    phone: str
    date_of_birth: Optional[str] = None
    nationality: Optional[str] = None
    current_address: Optional[str] = None
    marital_status: Optional[str] = None
    occupation: Optional[str] = None
    
    emergency_name: Optional[str] = None
    emergency_relationship: Optional[str] = None
    emergency_phone: Optional[str] = None
    emergency_email: Optional[str] = None
    
    medical_conditions: Optional[str] = None
    medications: Optional[str] = None
    allergies: Optional[str] = None
    doctor_name: Optional[str] = None
    doctor_phone: Optional[str] = None
    
    preferred_move_date: Optional[str] = None
    preferred_country: Optional[str] = None
    preferred_facility: Optional[str] = None
    special_requirements: Optional[str] = None

class ApplicationUpdate(BaseModel):
    status: Optional[str] = None
    notes: Optional[str] = None
    full_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    # ... other fields can be updated too

class ApplicationResponse(BaseModel):
    id: int
    lead_id: int
    full_name: str
    email: str
    phone: str
    date_of_birth: Optional[str]
    nationality: Optional[str]
    current_address: Optional[str]
    marital_status: Optional[str]
    occupation: Optional[str]
    
    emergency_name: Optional[str]
    emergency_relationship: Optional[str]
    emergency_phone: Optional[str]
    emergency_email: Optional[str]
    
    medical_conditions: Optional[str]
    medications: Optional[str]
    allergies: Optional[str]
    doctor_name: Optional[str]
    doctor_phone: Optional[str]
    
    preferred_move_date: Optional[str]
    preferred_country: Optional[str]
    preferred_facility: Optional[str]
    special_requirements: Optional[str]
    
    status: str
    notes: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]
    submitted_at: Optional[datetime]
    
    lead_name: Optional[str] = None
    lead_email: Optional[str] = None
    
    class Config:
        from_attributes = True

class DocumentResponse(BaseModel):
    id: int
    application_id: int
    document_type: str
    file_name: str
    file_path: str
    file_size: Optional[int]
    file_type: Optional[str]
    uploaded_at: datetime
    
    class Config:
        from_attributes = True