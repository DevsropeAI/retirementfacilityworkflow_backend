from fastapi import APIRouter, HTTPException, Depends, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc, func
from datetime import datetime
from typing import Optional, List
from app.core.database import get_db
from app.models.db_models import Lead, LeadStatus
from app.schemas.lead import LeadCreate, LeadUpdate, LeadResponse
from app.services.notification_service import create_notification
from app.models.db_models import Staff
from app.core.security import decode_token
from app.services.qualification_service import score_lead
from app.services.followup_service import send_welcome, send_score_followup
from app.services.application_token_service import generate_application_token, generate_application_link
from app.services.email_service import send_application_link
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import json

router = APIRouter()
security = HTTPBearer()

def get_current_staff(token: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)):
    """Verify JWT token and return staff_id"""
    payload = decode_token(token.credentials)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    return payload.get("id")


# ============ CREATE LEAD ============
@router.post("/", response_model=LeadResponse)
def create_lead(lead: LeadCreate, db: Session = Depends(get_db)):
    # Check if lead already exists
    existing = db.query(Lead).filter(Lead.email == lead.email).first()
    if existing:
        for key, value in lead.dict(exclude_unset=True).items():
            setattr(existing, key, value)
        existing.updated_at = func.now()
        db.commit()
        db.refresh(existing)
        
        # Auto-qualify on update
        try:
            qualification = score_lead(existing.__dict__)
            existing.qualification_score = qualification["score"]
            existing.qualification_reasoning = qualification["reasoning"]
            db.commit()
            db.refresh(existing)
        except Exception as e:
            print(f"Qualification failed: {e}")
        
        return existing
    
    # Create new lead
    db_lead = Lead(**lead.dict())
    db.add(db_lead)
    db.commit()
    db.refresh(db_lead)

    #  Auto-qualify the lead FIRST
    try:
        qualification = score_lead(db_lead.__dict__)
        db_lead.qualification_score = qualification["score"]
        db_lead.qualification_reasoning = qualification["reasoning"]
        db.commit()
        db.refresh(db_lead)
        print(f" Lead qualified: {db_lead.qualification_score}")
    except Exception as e:
        print(f" Qualification failed: {e}")
    
    #  THEN send follow-ups (now qualification_score is set)
    # Auto-trigger: Send Welcome Email
    try:
        result = send_welcome(db_lead, db)
        print(f" Welcome email result: {result}")
    except Exception as e:
        print(f" Welcome email failed: {e}")

    # Auto-trigger: Send Score Follow-up
    try:
        if db_lead.qualification_score:
            result = send_score_followup(db_lead, db)
            print(f" Score follow-up result: {result}")
        else:
            print(" No qualification score available, skipping follow-up")
    except Exception as e:
        print(f" Score follow-up failed: {e}")

    #  Send notification for Hot leads
    try:
        if db_lead.qualification_score == "Hot":
            # Notify all staff
            staff_list = db.query(Staff).filter(Staff.is_active == 1).all()
            for staff in staff_list:
                create_notification(
                    db=db,
                    staff_id=staff.id,
                    title="🔥 New Hot Lead",
                    message=f"{db_lead.name} — a new Hot lead has been captured!",
                    type="lead_created",
                    link=f"/leads/{db_lead.id}"
                )
    except Exception as e:
        print(f"Notification failed: {e}")    
        
    return db_lead


# ============ LIST LEADS ============
@router.get("/", response_model=List[LeadResponse])
def get_leads(
    db: Session = Depends(get_db),
    status: Optional[str] = None,
    search: Optional[str] = None,
    limit: int = 100,
    offset: int = 0
):
    """Get all leads with optional filters"""
    query = db.query(Lead)
    
    # Filter by status
    if status:
        query = query.filter(Lead.status == status)
    
    # Search by name or email
    if search:
        query = query.filter(
            (Lead.name.ilike(f"%{search}%")) | 
            (Lead.email.ilike(f"%{search}%"))
        )
    
    # Order by newest first
    query = query.order_by(desc(Lead.created_at))
    
    # Pagination
    query = query.offset(offset).limit(limit)
    
    return query.all()


# ============ GET SINGLE LEAD ============
@router.get("/{lead_id}", response_model=LeadResponse)
def get_lead(lead_id: int, db: Session = Depends(get_db)):
    """Get a single lead by ID"""
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    return lead


# ============ UPDATE LEAD ============
@router.put("/{lead_id}", response_model=LeadResponse)
def update_lead(
    lead_id: int,
    lead_update: LeadUpdate,
    db: Session = Depends(get_db),
    staff_id: int = Depends(get_current_staff)
):
    """Update a lead (status, assigned_to, notes, qualification)"""
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    
    # Update only provided fields
    update_data = lead_update.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(lead, key, value)
    
    # Add to communication history if status changed
    if "status" in update_data:
        history_entry = {
            "date": datetime.now().isoformat(),
            "type": "status_change",
            "message": f"Status changed to: {update_data['status']}",
            "by": staff_id
        }
        if not lead.communication_history:
            lead.communication_history = []
        lead.communication_history.append(history_entry)
    
    lead.updated_at = func.now()
    db.commit()
    db.refresh(lead)
    return lead


# ============ DELETE LEAD ============
@router.delete("/{lead_id}")
def delete_lead(
    lead_id: int,
    db: Session = Depends(get_db),
    staff_id: int = Depends(get_current_staff)
):
    """Delete a lead (admin only)"""
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    
    db.delete(lead)
    db.commit()
    return {"message": "Lead deleted successfully"}


# ============ ADD COMMUNICATION ============
@router.post("/{lead_id}/communication")
def add_communication(
    lead_id: int,
    communication: dict,
    db: Session = Depends(get_db),
    staff_id: int = Depends(get_current_staff)
):
    """Add a communication history entry"""
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    
    if not lead.communication_history:
        lead.communication_history = []
    
    entry = {
        "date": datetime.now().isoformat(),
        "type": communication.get("type", "note"),
        "message": communication.get("message", ""),
        "by": staff_id
    }
    lead.communication_history.append(entry)
    db.commit()
    db.refresh(lead)
    return lead


# ============ RE-QUALIFY LEAD ============
@router.post("/{lead_id}/requalify")
def requalify_lead(
    lead_id: int,
    db: Session = Depends(get_db),
    staff_id: int = Depends(get_current_staff)
):
    """Manually re-run AI qualification on a lead"""
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    
    try:
        qualification = score_lead(lead.__dict__)
        lead.qualification_score = qualification["score"]
        lead.qualification_reasoning = qualification["reasoning"]
        lead.updated_at = func.now()
        
        # ✅ Send follow-up after scoring
        if lead.qualification_score:
            try:
                result = send_score_followup(lead, db)
                print(f"✅ Re-qualify follow-up result: {result}")
            except Exception as e:
                print(f"❌ Score follow-up failed: {e}")
        
        # Add to communication history
        if not lead.communication_history:
            lead.communication_history = []
        lead.communication_history.append({
            "date": datetime.now().isoformat(),
            "type": "requalify",
            "message": f"Re-qualified: {qualification['score']} - {qualification['reasoning'][:100]}...",
            "by": staff_id
        })
        
        db.commit()
        db.refresh(lead)
        return {
            "score": lead.qualification_score,
            "reasoning": lead.qualification_reasoning
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Qualification failed: {str(e)}")



# ============ SEND APPLICATION ============
@router.post("/{lead_id}/send-application")
def send_application(
    lead_id: int,
    db: Session = Depends(get_db),
    staff_id: int = Depends(get_current_staff)
):
    """
    Generate application token and send application link to lead.
    Updates lead status to 'application'.
    """
    # Check if lead exists
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    
    # Check if application already exists for this lead
    from app.models.db_models import Application
    existing_application = db.query(Application).filter(Application.lead_id == lead_id).first()
    if existing_application:
        raise HTTPException(
            status_code=400, 
            detail="An application already exists for this lead"
        )
    
    # Generate token if it doesn't exist
    if not lead.application_token:
        from app.services.application_token_service import generate_application_token
        lead.application_token = generate_application_token(lead_id)
    
    # Generate application link
    from app.services.application_token_service import generate_application_link
    link = generate_application_link(lead.application_token)
    
    # Send email with the link
    from app.services.email_service import send_application_link
    email_success, email_msg = send_application_link(lead.email, lead.name, link)
    
    if not email_success:
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to send email: {email_msg}"
        )
    
    # ✅ Update lead status to "application"
    lead.status = LeadStatus.APPLICATION
    lead.application_sent_at = datetime.now()
    lead.application_status = "sent"
    db.commit()
    db.refresh(lead)
    
    # Log in communication history
    if not lead.communication_history:
        lead.communication_history = []
    lead.communication_history.append({
        "date": datetime.now().isoformat(),
        "type": "application_invite",
        "message": f"Application link sent to {lead.email}",
        "by": staff_id
    })
    db.commit()
    
    return {
        "message": "Application link sent successfully",
        "link": link,
        "token": lead.application_token
    }