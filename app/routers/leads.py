from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from app.core.database import get_db
from app.models.db_models import Lead, LeadStatus

router = APIRouter()

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
    status: str
    qualification_score: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True

@router.post("/", response_model=LeadResponse)
def create_lead(lead: LeadCreate, db: Session = Depends(get_db)):
    db_lead = Lead(**lead.dict())
    db.add(db_lead)
    db.commit()
    db.refresh(db_lead)
    return db_lead

@router.get("/", response_model=list[LeadResponse])
def get_leads(db: Session = Depends(get_db)):
    return db.query(Lead).order_by(Lead.created_at.desc()).all()

@router.get("/{lead_id}", response_model=LeadResponse)
def get_lead(lead_id: int, db: Session = Depends(get_db)):
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    return lead