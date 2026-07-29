from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from sqlalchemy import desc, func
from typing import Optional, List
from datetime import date, datetime
import os
import uuid
import base64
import hashlib
import time
from pathlib import Path

from app.core.database import get_db
from app.models.db_models import Agreement, AgreementStatus, Lead, Application
from app.schemas.agreement import AgreementCreate, AgreementUpdate, AgreementResponse, AgreementSignRequest
from app.core.security import decode_token
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.services.email_service import send_email
from app.services.agreement_pdf_service import generate_agreement_pdf

router = APIRouter()
security = HTTPBearer()

# ============ HELPER FUNCTIONS ============

def generate_agreement_number(lead_id: int) -> str:
    """Generate a unique agreement number"""
    timestamp = int(time.time())
    return f"AGR-{lead_id}-{timestamp}"

def generate_agreement_token(lead_id: int) -> str:
    """Generate a unique token for the agreement"""
    token_string = f"{lead_id}-{time.time()}-{uuid.uuid4()}"
    return hashlib.sha256(token_string.encode()).hexdigest()[:32]

def generate_agreement_link(token: str) -> str:
    """Generate the full agreement link"""
    return f"http://localhost:3000/sign-agreement/{token}"

def get_current_staff(token: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)):
    payload = decode_token(token.credentials)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    return payload.get("id")

# ============ STAFF ENDPOINTS ============

@router.post("/generate", response_model=AgreementResponse)
def generate_agreement(
    agreement: AgreementCreate,
    db: Session = Depends(get_db),
    staff_id: int = Depends(get_current_staff)
):
    """Generate a new agreement from application data"""
    
    # Check if lead exists
    lead = db.query(Lead).filter(Lead.id == agreement.lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    
    # Check if application exists and is approved
    if agreement.application_id:
        application = db.query(Application).filter(Application.id == agreement.application_id).first()
        if application and application.status != "approved":
            raise HTTPException(status_code=400, detail="Application must be approved to generate agreement")
    
    # Generate agreement number and token
    agreement_number = generate_agreement_number(agreement.lead_id)
    token = generate_agreement_token(agreement.lead_id)
    
    # Create agreement
    db_agreement = Agreement(
        lead_id=agreement.lead_id,
        application_id=agreement.application_id,
        agreement_number=agreement_number,
        facility=agreement.facility,
        room_number=agreement.room_number,
        move_in_date=agreement.move_in_date,
        monthly_fee=agreement.monthly_fee,
        security_deposit=agreement.security_deposit,
        terms_conditions=agreement.terms_conditions,
        token=token,
        status=AgreementStatus.DRAFT
    )
    
    db.add(db_agreement)
    db.commit()
    db.refresh(db_agreement)
    
    return db_agreement

@router.get("/", response_model=List[AgreementResponse])
def get_agreements(
    db: Session = Depends(get_db),
    status: Optional[str] = None,
    staff_id: int = Depends(get_current_staff)
):
    """Get all agreements (staff only)"""
    query = db.query(Agreement)
    
    if status:
        query = query.filter(Agreement.status == status)
    
    query = query.order_by(desc(Agreement.created_at))
    agreements = query.all()
    
    # Add lead info
    result = []
    for agreement in agreements:
        lead = agreement.lead
        response = AgreementResponse.from_orm(agreement)
        response.lead_name = lead.name if lead else None
        response.lead_email = lead.email if lead else None
        response.lead_phone = lead.phone if lead else None
        result.append(response)
    
    return result

@router.get("/{agreement_id}", response_model=AgreementResponse)
def get_agreement(
    agreement_id: int,
    db: Session = Depends(get_db),
    staff_id: int = Depends(get_current_staff)
):
    """Get a single agreement"""
    agreement = db.query(Agreement).filter(Agreement.id == agreement_id).first()
    if not agreement:
        raise HTTPException(status_code=404, detail="Agreement not found")
    
    lead = agreement.lead
    response = AgreementResponse.from_orm(agreement)
    response.lead_name = lead.name if lead else None
    response.lead_email = lead.email if lead else None
    response.lead_phone = lead.phone if lead else None
    
    return response

@router.put("/{agreement_id}", response_model=AgreementResponse)
def update_agreement(
    agreement_id: int,
    agreement_update: AgreementUpdate,
    db: Session = Depends(get_db),
    staff_id: int = Depends(get_current_staff)
):
    """Update agreement details"""
    agreement = db.query(Agreement).filter(Agreement.id == agreement_id).first()
    if not agreement:
        raise HTTPException(status_code=404, detail="Agreement not found")
    
    update_data = agreement_update.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(agreement, key, value)
    
    db.commit()
    db.refresh(agreement)
    
    return agreement

@router.post("/{agreement_id}/send")
def send_agreement_to_lead(
    agreement_id: int,
    db: Session = Depends(get_db),
    staff_id: int = Depends(get_current_staff)
):
    """Send agreement link to lead"""
    print(f"📤 Sending agreement {agreement_id}...")
    
    agreement = db.query(Agreement).filter(Agreement.id == agreement_id).first()
    if not agreement:
        print(f"❌ Agreement {agreement_id} not found")
        raise HTTPException(status_code=404, detail="Agreement not found")
    
    lead = agreement.lead
    if not lead:
        print(f"❌ Lead not found for agreement {agreement_id}")
        raise HTTPException(status_code=404, detail="Lead not found")
    
    print(f"👤 Lead: {lead.name} ({lead.email})")
    
    # Generate token if not exists
    if not agreement.token:
        print("🔑 Generating new token...")
        agreement.token = generate_agreement_token(agreement.lead_id)
    
    link = generate_agreement_link(agreement.token)
    print(f"🔗 Link: {link}")
    
    # Send email
    subject = "Please Sign Your Residency Agreement — Retirees Paradise"
    
    body = f"""
Dear {lead.name},

Your residency agreement is ready for review and signature.

Click the link below to review and sign your agreement:
{link}

If you have any questions, please contact our team.

Best regards,
The Retirees Paradise Team
"""
    
    html_body = f"""
<h2>Sign Your Residency Agreement</h2>
<p>Dear {lead.name},</p>
<p>Your residency agreement is ready for review and signature.</p>
<p><a href="{link}" style="display: inline-block; background-color: #2563eb; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; font-weight: 600;">Review & Sign Agreement</a></p>
<p>If you have any questions, please contact our team.</p>
<p>Best regards,<br>The Retirees Paradise Team</p>
"""
    
    print(f"📧 Sending email to {lead.email}...")
    success, msg = send_email(lead.email, subject, body, html_body)
    print(f"📧 Result: success={success}, msg={msg}")
    
    if not success:
        print(f"❌ Email failed: {msg}")
        raise HTTPException(status_code=500, detail=f"Failed to send email: {msg}")
    
    agreement.status = AgreementStatus.PENDING
    agreement.sent_at = datetime.now()
    db.commit()
    
    print(f"✅ Agreement {agreement_id} sent successfully")
    return {"message": "Agreement sent successfully", "link": link}

@router.get("/{agreement_id}/download")
def download_agreement(
    agreement_id: int,
    db: Session = Depends(get_db),
    staff_id: int = Depends(get_current_staff)
):
    """Download signed agreement PDF"""
    agreement = db.query(Agreement).filter(Agreement.id == agreement_id).first()
    if not agreement:
        raise HTTPException(status_code=404, detail="Agreement not found")
    
    if not agreement.signed_pdf_path:
        raise HTTPException(status_code=404, detail="Signed agreement not found")
    
    backend_root = Path(__file__).parent.parent.parent
    file_path = backend_root / agreement.signed_pdf_path
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    
    return FileResponse(
        path=file_path,
        filename=f"agreement_{agreement.agreement_number}.pdf",
        media_type="application/pdf"
    )

# ============ PUBLIC ENDPOINTS (Client) ============

@router.get("/public/{token}")
def get_agreement_by_token(
    token: str,
    db: Session = Depends(get_db)
):
    """Get agreement by token for client signing"""
    agreement = db.query(Agreement).filter(Agreement.token == token).first()
    if not agreement:
        raise HTTPException(status_code=404, detail="Agreement not found")
    
    if agreement.status in [AgreementStatus.SIGNED, AgreementStatus.EXPIRED, AgreementStatus.CANCELLED]:
        raise HTTPException(status_code=400, detail="This agreement is no longer available for signing")
    
    lead = agreement.lead
    
    return {
        "id": agreement.id,
        "lead_name": lead.name if lead else None,
        "lead_email": lead.email if lead else None,
        "facility": agreement.facility,
        "room_number": agreement.room_number,
        "move_in_date": agreement.move_in_date,
        "monthly_fee": agreement.monthly_fee,
        "security_deposit": agreement.security_deposit,
        "terms_conditions": agreement.terms_conditions,
        "agreement_number": agreement.agreement_number
    }

@router.post("/public/sign/{token}")
def sign_agreement(
    token: str,
    sign_data: AgreementSignRequest,
    db: Session = Depends(get_db)
):
    """Lead signs the agreement"""
    agreement = db.query(Agreement).filter(Agreement.token == token).first()
    if not agreement:
        raise HTTPException(status_code=404, detail="Agreement not found")
    
    if agreement.status in [AgreementStatus.SIGNED, AgreementStatus.EXPIRED, AgreementStatus.CANCELLED]:
        raise HTTPException(status_code=400, detail="This agreement is no longer available for signing")
    
    # Save signature
    agreement.signature_image = sign_data.signature_image
    agreement.status = AgreementStatus.SIGNED
    agreement.signed_at = datetime.now()
    
    # Generate PDF
    try:
        pdf_path = generate_agreement_pdf(agreement)
        agreement.signed_pdf_path = pdf_path
    except Exception as e:
        print(f"PDF generation failed: {e}")
        # Continue without PDF (we can generate later)
    
    db.commit()
    
    # Update lead status
    lead = agreement.lead
    if lead:
        lead.status = "enrolled"
        db.commit()
    
    return {"message": "Agreement signed successfully", "agreement_id": agreement.id}