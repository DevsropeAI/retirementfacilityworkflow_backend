from pydantic import BaseModel
from typing import Optional, List, Dict
from datetime import datetime

class LeadCreate(BaseModel):
    name: str
    email: str
    phone: str
    age: Optional[int] = None
    current_location: Optional[str] = None
    retirement_status: Optional[str] = None
    monthly_income: Optional[float] = None
    desired_move_date: Optional[str] = None
    desired_country: Optional[str] = None
    budget: Optional[str] = None
    timeline: Optional[str] = None
    medical_requirements: Optional[str] = None
    family_info: Optional[str] = None
    lead_source: Optional[str] = "landing_page"

class LeadUpdate(BaseModel):
    status: Optional[str] = None
    assigned_to: Optional[int] = None
    notes: Optional[str] = None
    qualification_score: Optional[str] = None
    qualification_reasoning: Optional[str] = None

class LeadResponse(BaseModel):
    id: int
    name: str
    email: str
    phone: str
    age: Optional[int]
    current_location: Optional[str]
    retirement_status: Optional[str]
    monthly_income: Optional[float]
    desired_move_date: Optional[str]
    desired_country: Optional[str]
    budget: Optional[str]
    timeline: Optional[str]
    medical_requirements: Optional[str]
    family_info: Optional[str]
    lead_source: str
    status: str
    assigned_to: Optional[int]
    notes: Optional[str]
    communication_history: List[Dict]
    qualification_score: Optional[str]
    qualification_reasoning: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]
    
    class Config:
        from_attributes = True