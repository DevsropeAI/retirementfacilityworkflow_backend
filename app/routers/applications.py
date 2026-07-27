from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import Optional, List
import os
import shutil
import uuid
from datetime import datetime
from app.core.database import get_db
from app.models.db_models import Application, ApplicationStatus, Lead, Document
from app.schemas.application import ApplicationCreate, ApplicationUpdate, ApplicationResponse, DocumentResponse
from app.core.security import decode_token
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

router = APIRouter()
security = HTTPBearer()

# ============ HELPER FUNCTIONS ============

UPLOAD_DIR = "uploads/documents"

def get_current_staff(token: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)):
    payload = decode_token(token.credentials)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    return payload.get("id")

def generate_application_token(lead_id: int) -> str:
    """Generate a unique token for the client portal"""
    import hashlib
    import time
    token_string = f"{lead_id}-{time.time()}-{uuid.uuid4()}"
    return hashlib.sha256(token_string.encode()).hexdigest()[:32]

def save_uploaded_file(upload_file: UploadFile, document_type: str, application_id: int) -> str:
    """Save uploaded file to disk and return file path"""
    # Create upload directory if it doesn't exist
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    
    # Generate unique filename
    file_extension = os.path.splitext(upload_file.filename)[1]
    unique_filename = f"{application_id}_{document_type}_{uuid.uuid4().hex[:8]}{file_extension}"
    file_path = os.path.join(UPLOAD_DIR, unique_filename)
    
    # Save file
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(upload_file.file, buffer)
    
    return file_path

# ============ PUBLIC ENDPOINTS (Client Portal) ============

@router.post("/public/submit")
def submit_application(
    application: ApplicationCreate,
    db: Session = Depends(get_db)
):
    """Submit application from client portal"""
    # Check if lead exists
    lead = db.query(Lead).filter(Lead.id == application.lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    
    # Create application
    db_application = Application(**application.dict())
    db_application.status = ApplicationStatus.SUBMITTED
    db_application.submitted_at = datetime.now()
    
    # Update lead status
    lead.status = "application"
    
    db.add(db_application)
    db.commit()
    db.refresh(db_application)
    
    return {"message": "Application submitted successfully", "application_id": db_application.id}

@router.post("/public/upload/{application_id}")
def upload_document(
    application_id: int,
    document_type: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """Upload a document for an application"""
    application = db.query(Application).filter(Application.id == application_id).first()
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")
    
    # Save file
    file_path = save_uploaded_file(file, document_type, application_id)
    
    # Create document record
    document = Document(
        application_id=application_id,
        document_type=document_type,
        file_name=file.filename,
        file_path=file_path,
        file_size=os.path.getsize(file_path),
        file_type=file.content_type
    )
    
    db.add(document)
    db.commit()
    db.refresh(document)
    
    return {"message": "Document uploaded successfully", "document": DocumentResponse.from_orm(document)}

# ============ STAFF ENDPOINTS ============

@router.get("/", response_model=List[ApplicationResponse])
def get_applications(
    db: Session = Depends(get_db),
    status: Optional[str] = None,
    staff_id: int = Depends(get_current_staff)
):
    """Get all applications (staff only)"""
    query = db.query(Application)
    
    if status:
        query = query.filter(Application.status == status)
    
    query = query.order_by(desc(Application.created_at))
    applications = query.all()
    
    # Add lead info
    result = []
    for app in applications:
        lead = app.lead
        response = ApplicationResponse.from_orm(app)
        response.lead_name = lead.name if lead else None
        response.lead_email = lead.email if lead else None
        result.append(response)
    
    return result

@router.get("/{application_id}", response_model=ApplicationResponse)
def get_application(
    application_id: int,
    db: Session = Depends(get_db),
    staff_id: int = Depends(get_current_staff)
):
    """Get a single application with documents"""
    application = db.query(Application).filter(Application.id == application_id).first()
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")
    
    lead = application.lead
    response = ApplicationResponse.from_orm(application)
    response.lead_name = lead.name if lead else None
    response.lead_email = lead.email if lead else None
    
    return response

@router.get("/{application_id}/documents", response_model=List[DocumentResponse])
def get_application_documents(
    application_id: int,
    db: Session = Depends(get_db),
    staff_id: int = Depends(get_current_staff)
):
    """Get all documents for an application"""
    documents = db.query(Document).filter(Document.application_id == application_id).all()
    return documents

@router.put("/{application_id}", response_model=ApplicationResponse)
def update_application(
    application_id: int,
    application_update: ApplicationUpdate,
    db: Session = Depends(get_db),
    staff_id: int = Depends(get_current_staff)
):
    """Update application status or details (staff only)"""
    application = db.query(Application).filter(Application.id == application_id).first()
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")
    
    update_data = application_update.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(application, key, value)
    
    db.commit()
    db.refresh(application)
    
    return application

@router.post("/{application_id}/approve")
def approve_application(
    application_id: int,
    notes: Optional[str] = None,
    db: Session = Depends(get_db),
    staff_id: int = Depends(get_current_staff)
):
    """Approve an application"""
    application = db.query(Application).filter(Application.id == application_id).first()
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")
    
    application.status = ApplicationStatus.APPROVED
    if notes:
        application.notes = notes
    
    # Update lead status
    lead = application.lead
    if lead:
        lead.status = "approved"
    
    db.commit()
    db.refresh(application)
    
    return {"message": "Application approved", "application_id": application.id}

@router.post("/{application_id}/reject")
def reject_application(
    application_id: int,
    notes: Optional[str] = None,
    db: Session = Depends(get_db),
    staff_id: int = Depends(get_current_staff)
):
    """Reject an application"""
    application = db.query(Application).filter(Application.id == application_id).first()
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")
    
    application.status = ApplicationStatus.REJECTED
    if notes:
        application.notes = notes
    
    db.commit()
    db.refresh(application)
    
    return {"message": "Application rejected", "application_id": application.id}