from sqlalchemy import Column, Integer, String, DateTime, Text, Enum, JSON, Float
from sqlalchemy.sql import func
from app.core.database import Base
import enum

class LeadStatus(str, enum.Enum):
    NEW = "new"
    CONTACTED = "contacted"
    QUALIFIED = "qualified"
    CONSULTATION = "consultation"
    APPLICATION = "application"
    APPROVED = "approved"
    ENROLLED = "enrolled"
    REJECTED = "rejected"

class Lead(Base):
    __tablename__ = "leads"

    id = Column(Integer, primary_key=True, index=True)
    
    # Personal Info
    name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False, index=True)
    phone = Column(String(50), nullable=False)
    age = Column(Integer, nullable=True)
    current_location = Column(String(255), nullable=True)
    retirement_status = Column(String(100), nullable=True)
    monthly_income = Column(Float, nullable=True)
    desired_move_date = Column(String(50), nullable=True)
    desired_country = Column(String(100), nullable=True)
    budget = Column(String(100), nullable=True)
    timeline = Column(String(100), nullable=True)
    medical_requirements = Column(Text, nullable=True)
    family_info = Column(Text, nullable=True)
    
    # CRM Fields
    lead_source = Column(String(100), default="landing_page")
    status = Column(Enum(LeadStatus), default=LeadStatus.NEW)
    assigned_to = Column(String(255), nullable=True)
    
    # Qualification
    qualification_score = Column(String(20), nullable=True)  # Hot/Warm/Cold
    qualification_reasoning = Column(Text, nullable=True)
    
    # Communication
    communication_history = Column(JSON, default=list)
    notes = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class Staff(Base):
    __tablename__ = "staff"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(50), default="staff")  # admin / staff
    is_active = Column(Integer, default=1)
    created_at = Column(DateTime(timezone=True), server_default=func.now())