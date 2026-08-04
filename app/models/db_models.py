from sqlalchemy import Column, Integer, String, DateTime, Text, Enum, JSON, Float, ForeignKey, Date
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
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
    
    # Personal Information (from form)
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
    
    # CRM Fields (from workflow)
    lead_source = Column(String(100), default="landing_page")
    status = Column(Enum(LeadStatus), default=LeadStatus.NEW)
    assigned_to = Column(Integer, ForeignKey("staff.id"), nullable=True)
    
    # Communication & Notes
    communication_history = Column(JSON, default=list)
    notes = Column(Text, nullable=True)
    
    # AI Qualification
    qualification_score = Column(String(20), nullable=True)  # Hot/Warm/Cold
    qualification_reasoning = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationship
    assigned_staff = relationship("Staff", foreign_keys=[assigned_to])

    #application fields
    application_token = Column(String(64), nullable=True, unique=True)
    application_sent_at = Column(DateTime(timezone=True), nullable=True)
    application_status = Column(String(50), default="not_sent")

class Consultation(Base):
    __tablename__ = "consultations"

    id = Column(Integer, primary_key=True, index=True)
    lead_id = Column(Integer, ForeignKey("leads.id"), nullable=False)
    
    # Consultation Details
    consultation_type = Column(String(50), nullable=False)  # phone, zoom, facility_tour
    scheduled_date = Column(DateTime, nullable=False)
    scheduled_time = Column(String(20), nullable=False)  # e.g., "10:00 AM"
    duration = Column(Integer, default=60)  # minutes
    notes = Column(Text, nullable=True)
    
    # Status
    status = Column(String(50), default="scheduled")  # scheduled, completed, cancelled, no_show
    
    # Zoom/Meeting details (optional)
    meeting_link = Column(String(500), nullable=True)
    meeting_id = Column(String(100), nullable=True)
    
    # Reminders
    reminder_sent = Column(Integer, default=0)  # 0 = not sent, 1 = sent
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationship
    lead = relationship("Lead", backref="consultations")


class Staff(Base):
    __tablename__ = "staff"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(50), default="staff")  # admin / staff
    is_active = Column(Integer, default=1)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    staff_id = Column(Integer, ForeignKey("staff.id"), nullable=False)
    
    # Notification Details
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    type = Column(String(50), nullable=False)  # consultation_booked, lead_created, reminder, status_change
    link = Column(String(500), nullable=True)  # URL to navigate to
    
    # Status
    is_read = Column(Integer, default=0)  # 0 = unread, 1 = read
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationship
    staff = relationship("Staff", backref="notifications")

class ApplicationStatus(str, enum.Enum):
    DRAFT = "draft"
    SUBMITTED = "submitted"
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    COMPLETED = "completed"

class Application(Base):
    __tablename__ = "applications"

    id = Column(Integer, primary_key=True, index=True)
    lead_id = Column(Integer, ForeignKey("leads.id"), nullable=False)
    
    # Personal Information
    full_name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False, index=True)
    phone = Column(String(50), nullable=False)
    date_of_birth = Column(String(50), nullable=True)
    nationality = Column(String(100), nullable=True)
    current_address = Column(Text, nullable=True)
    marital_status = Column(String(50), nullable=True)
    occupation = Column(String(100), nullable=True)
    
    # Emergency Contact
    emergency_name = Column(String(255), nullable=True)
    emergency_relationship = Column(String(100), nullable=True)
    emergency_phone = Column(String(50), nullable=True)
    emergency_email = Column(String(255), nullable=True)
    
    # Medical Information
    medical_conditions = Column(Text, nullable=True)
    medications = Column(Text, nullable=True)
    allergies = Column(Text, nullable=True)
    doctor_name = Column(String(255), nullable=True)
    doctor_phone = Column(String(50), nullable=True)
    
    # Preferences
    preferred_move_date = Column(String(50), nullable=True)
    preferred_country = Column(String(100), nullable=True)
    preferred_facility = Column(String(255), nullable=True)
    special_requirements = Column(Text, nullable=True)
    
    # Status
    status = Column(Enum(ApplicationStatus), default=ApplicationStatus.DRAFT)
    notes = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    submitted_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationship
    lead = relationship("Lead", backref="applications")

class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    application_id = Column(Integer, ForeignKey("applications.id"), nullable=False)
    
    document_type = Column(String(50), nullable=False)  # passport, id_card, medical, insurance
    file_name = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_size = Column(Integer, nullable=True)
    file_type = Column(String(100), nullable=True)
    
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationship
    application = relationship("Application", backref="documents")    

class AgreementStatus(str, enum.Enum):
    DRAFT = "draft"
    PENDING = "pending"      # Sent to lead
    SIGNED = "signed"        # Lead signed
    EXPIRED = "expired"
    CANCELLED = "cancelled"

class Agreement(Base):
    __tablename__ = "agreements"

    id = Column(Integer, primary_key=True, index=True)
    lead_id = Column(Integer, ForeignKey("leads.id"), nullable=False)
    application_id = Column(Integer, ForeignKey("applications.id"), nullable=True)
    
    # Agreement Details
    agreement_number = Column(String(50), nullable=False, unique=True)
    facility = Column(String(255), nullable=False)
    room_number = Column(String(50), nullable=True)
    move_in_date = Column(Date, nullable=False)
    monthly_fee = Column(Float, nullable=False)
    security_deposit = Column(Float, nullable=True)
    terms_conditions = Column(Text, nullable=True)
    
    # Status
    status = Column(Enum(AgreementStatus), default=AgreementStatus.DRAFT)
    
    # Token for client access
    token = Column(String(64), nullable=True, unique=True)
    
    # Signature
    signature_image = Column(Text, nullable=True)  # Base64 image
    signed_at = Column(DateTime(timezone=True), nullable=True)
    signed_pdf_path = Column(String(500), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    sent_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    lead = relationship("Lead", backref="agreements")
    application = relationship("Application", backref="agreements")    