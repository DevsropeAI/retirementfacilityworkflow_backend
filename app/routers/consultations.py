from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import desc, func
from datetime import datetime, timedelta
from typing import Optional, List
from app.core.database import get_db
from app.models.db_models import Consultation, Lead, LeadStatus
from app.schemas.consultation import ConsultationCreate, ConsultationUpdate, ConsultationResponse
from app.services.notification_service import create_notification
from app.models.db_models import Staff
from datetime import datetime, timedelta
from app.services.notification_service import create_notification
from app.models.db_models import Staff
from app.core.security import decode_token
from app.services.email_service import send_email
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import logging

logger = logging.getLogger(__name__)

router = APIRouter()
security = HTTPBearer()

def get_current_staff(token: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)):
    payload = decode_token(token.credentials)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    return payload.get("id")


def send_consultation_confirmation(consultation: Consultation, lead: Lead):
    """Send confirmation email to lead"""
    date_str = consultation.scheduled_date.strftime("%B %d, %Y")
    time_str = consultation.scheduled_time
    
    type_labels = {
        "phone": "📞 Phone Call",
        "zoom": "💻 Zoom Meeting",
        "facility_tour": "🏢 Facility Tour"
    }
    type_label = type_labels.get(consultation.consultation_type, consultation.consultation_type)
    
    subject = f"Your Consultation is Confirmed — Retirees Paradise"
    
    body = f"""
Dear {lead.name},

Your consultation with Retirees Paradise has been confirmed!

📅 Date: {date_str}
⏰ Time: {time_str}
📋 Type: {type_label}
🕐 Duration: {consultation.duration} minutes

{f"🔗 Meeting Link: {consultation.meeting_link}" if consultation.meeting_link else ""}

What to expect:
• A brief introduction to our retirement communities
• Discussion of your preferences and needs
• Q&A about the relocation process
• Next steps for your retirement journey

{f"📝 Notes: {consultation.notes}" if consultation.notes else ""}

If you need to reschedule or have any questions, please reply to this email or call us at +1-800-555-0123.

We look forward to speaking with you!

Best regards,
The Retirees Paradise Team
"""
    
    html_body = f"""
<h2>Your Consultation is Confirmed</h2>
<p>Dear {lead.name},</p>
<p>Your consultation with Retirees Paradise has been confirmed!</p>

<table style="border-collapse: collapse; width: 100%; max-width: 500px;">
  <tr><td style="padding: 8px 0;"><strong>📅 Date:</strong></td><td>{date_str}</td></tr>
  <tr><td style="padding: 8px 0;"><strong>⏰ Time:</strong></td><td>{time_str}</td></tr>
  <tr><td style="padding: 8px 0;"><strong>📋 Type:</strong></td><td>{type_label}</td></tr>
  <tr><td style="padding: 8px 0;"><strong>🕐 Duration:</strong></td><td>{consultation.duration} minutes</td></tr>
  {f'<tr><td style="padding: 8px 0;"><strong>🔗 Meeting Link:</strong></td><td><a href="{consultation.meeting_link}">{consultation.meeting_link}</a></td></tr>' if consultation.meeting_link else ''}
</table>

<h3>What to expect:</h3>
<ul>
  <li>A brief introduction to our retirement communities</li>
  <li>Discussion of your preferences and needs</li>
  <li>Q&A about the relocation process</li>
  <li>Next steps for your retirement journey</li>
</ul>

{f'<p><strong>📝 Notes:</strong> {consultation.notes}</p>' if consultation.notes else ''}

<p>If you need to reschedule or have any questions, please reply to this email or call us at +1-800-555-0123.</p>

<p>We look forward to speaking with you!</p>
<p>Best regards,<br>The Retirees Paradise Team</p>
"""
    
    success, msg = send_email(lead.email, subject, body, html_body)
    logger.info(f"Confirmation email sent to {lead.email}: {success}")
    return success, msg


def send_consultation_reminder(consultation: Consultation, lead: Lead, db: Session):
    """Send reminder email to lead and staff notification"""
    
    from datetime import datetime
    
    date_str = consultation.scheduled_date.strftime("%B %d, %Y")
    time_str = consultation.scheduled_time
    
    # ✅ Determine if reminder is for today or tomorrow
    today = datetime.now().date()
    consultation_date = consultation.scheduled_date.date()
    
    if consultation_date == today:
        reminder_text = "today"
    else:
        reminder_text = "tomorrow"
    
    # ============ 1. SEND LEAD EMAIL REMINDER ============
    subject = f"⏰ Reminder: Your Consultation {reminder_text.capitalize()} — Retirees Paradise"
    
    body = f"""
Dear {lead.name},

This is a friendly reminder about your consultation {reminder_text}!

📅 Date: {date_str}
⏰ Time: {time_str}
🕐 Duration: {consultation.duration} minutes

{f"🔗 Meeting Link: {consultation.meeting_link}" if consultation.meeting_link else ""}

We look forward to speaking with you!

Best regards,
The Retirees Paradise Team
"""
    
    html_body = f"""
<h2>⏰ Reminder: Your Consultation {reminder_text.capitalize()}</h2>
<p>Dear {lead.name},</p>
<p>This is a friendly reminder about your consultation {reminder_text}!</p>

<table style="border-collapse: collapse; width: 100%; max-width: 500px;">
  <tr><td style="padding: 8px 0;"><strong>📅 Date:</strong></td><td>{date_str}</td></tr>
  <tr><td style="padding: 8px 0;"><strong>⏰ Time:</strong></td><td>{time_str}</td></tr>
  <tr><td style="padding: 8px 0;"><strong>🕐 Duration:</strong></td><td>{consultation.duration} minutes</td></tr>
  {f'<tr><td style="padding: 8px 0;"><strong>🔗 Link:</strong></td><td><a href="{consultation.meeting_link}">{consultation.meeting_link}</a></td></tr>' if consultation.meeting_link else ''}
</table>

<p>We look forward to speaking with you!</p>
<p>Best regards,<br>The Retirees Paradise Team</p>
"""
    
    # Send email to lead
    email_success, email_msg = send_email(lead.email, subject, body, html_body)
    logger.info(f"Reminder email to {lead.email}: {email_success}")
    
    # ============ 2. SEND STAFF IN-APP NOTIFICATION ============
    try:
        staff_list = db.query(Staff).filter(Staff.is_active == 1).all()
        
        notification_count = 0
        for staff in staff_list:
            try:
                create_notification(
                    db=db,
                    staff_id=staff.id,
                    title=f"⏰ Consultation {reminder_text.capitalize()}",
                    message=f"Consultation with {lead.name} {reminder_text} at {time_str}",
                    type="reminder",
                    link=f"/leads/{lead.id}"
                )
                notification_count += 1
            except Exception as e:
                logger.error(f"Failed to create notification for staff {staff.id}: {e}")
        
        logger.info(f"Sent {notification_count} staff notifications for consultation {consultation.id}")
        
    except Exception as e:
        logger.error(f"Staff notification failed: {e}")
    
    # ============ 3. LOG IN COMMUNICATION HISTORY ============
    try:
        if not lead.communication_history:
            lead.communication_history = []
        
        lead.communication_history.append({
            "date": datetime.now().isoformat(),
            "type": "reminder_sent",
            "message": f"{reminder_text.capitalize()} reminder sent to lead ({email_success}) and {notification_count} staff members",
            "by": "system"
        })
        db.commit()
    except Exception as e:
        logger.error(f"Communication history logging failed: {e}")
    
    # ============ 4. MARK AS SENT ============
    consultation.reminder_sent = 1
    db.commit()
    
    return email_success, email_msg

# ============ CREATE CONSULTATION ============
@router.post("/", response_model=ConsultationResponse)
def create_consultation(
    consultation: ConsultationCreate,
    db: Session = Depends(get_db),
    staff_id: int = Depends(get_current_staff)
):
    """Book a consultation for a lead"""
    
    # Check if lead exists
    lead = db.query(Lead).filter(Lead.id == consultation.lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    
    # Parse date
    try:
        scheduled_date = datetime.fromisoformat(consultation.scheduled_date)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use ISO format (YYYY-MM-DD)")
    
    # Create consultation
    db_consultation = Consultation(
        lead_id=consultation.lead_id,
        consultation_type=consultation.consultation_type,
        scheduled_date=scheduled_date,
        scheduled_time=consultation.scheduled_time,
        duration=consultation.duration or 60,
        notes=consultation.notes,
        meeting_link=consultation.meeting_link,
        meeting_id=consultation.meeting_id,
        status="scheduled"
    )
    
    db.add(db_consultation)
    db.commit()
    db.refresh(db_consultation)
    
    #  Auto-update lead status to "consultation"
    if lead.status != LeadStatus.CONSULTATION:
        lead.status = LeadStatus.CONSULTATION
        lead.updated_at = func.now()
        
        # Add to communication history
        if not lead.communication_history:
            lead.communication_history = []
        lead.communication_history.append({
            "date": datetime.now().isoformat(),
            "type": "status_change",
            "message": f"Status changed to: consultation (via booking)",
            "by": staff_id
        })
        
        db.commit()
    
    #  Send confirmation email
    try:
        send_consultation_confirmation(db_consultation, lead)
    except Exception as e:
        logger.error(f"Confirmation email failed: {e}")
    
    #  Log in communication history
    if not lead.communication_history:
        lead.communication_history = []
    lead.communication_history.append({
        "date": datetime.now().isoformat(),
        "type": "consultation_booked",
        "message": f"Consultation booked: {consultation.consultation_type} on {consultation.scheduled_date} at {consultation.scheduled_time}",
        "by": staff_id
    })
    db.commit()

    #  Send staff notification (in-app)
    try:
        # Get the staff who booked it
        staff = db.query(Staff).filter(Staff.id == staff_id).first()
        if staff:
            create_notification(
                db=db,
                staff_id=staff_id,
                title="📅 New Consultation Booked",
                message=f"Consultation booked for {lead.name} on {scheduled_date.strftime('%B %d, %Y')} at {consultation.scheduled_time}",
                type="consultation_booked",
                link=f"/leads/{lead.id}"
            )
    except Exception as e:
        logger.error(f"Notification failed: {e}")
    
    return db_consultation


# ============ LIST CONSULTATIONS ============
@router.get("/", response_model=List[ConsultationResponse])
def get_consultations(
    db: Session = Depends(get_db),
    status: Optional[str] = None,
    upcoming: bool = True,
    limit: int = 50,
    offset: int = 0
):
    """Get all consultations with optional filters"""
    query = db.query(Consultation).options(joinedload(Consultation.lead))
    
    # Filter by status
    if status:
        query = query.filter(Consultation.status == status)
    
    # Upcoming only
    if upcoming:
        now = datetime.now()
        query = query.filter(Consultation.scheduled_date >= now)
        query = query.filter(Consultation.status == "scheduled")
    
    # Order by date (soonest first)
    query = query.order_by(Consultation.scheduled_date.asc())
    
    # Pagination
    query = query.offset(offset).limit(limit)
    
    consultations = query.all()
    
    # Add lead info to response
    result = []
    for c in consultations:
        lead = c.lead
        response = ConsultationResponse.from_orm(c)
        response.lead_name = lead.name if lead else None
        response.lead_email = lead.email if lead else None
        response.lead_phone = lead.phone if lead else None
        result.append(response)
    
    return result


# ============ GET SINGLE CONSULTATION ============
@router.get("/{consultation_id}", response_model=ConsultationResponse)
def get_consultation(
    consultation_id: int,
    db: Session = Depends(get_db)
):
    """Get a single consultation by ID"""
    consultation = db.query(Consultation).options(joinedload(Consultation.lead)).filter(
        Consultation.id == consultation_id
    ).first()
    
    if not consultation:
        raise HTTPException(status_code=404, detail="Consultation not found")
    
    lead = consultation.lead
    response = ConsultationResponse.from_orm(consultation)
    response.lead_name = lead.name if lead else None
    response.lead_email = lead.email if lead else None
    response.lead_phone = lead.phone if lead else None
    
    return response


# ============ UPDATE CONSULTATION ============
@router.put("/{consultation_id}", response_model=ConsultationResponse)
def update_consultation(
    consultation_id: int,
    consultation_update: ConsultationUpdate,
    db: Session = Depends(get_db),
    staff_id: int = Depends(get_current_staff)
):
    """Update a consultation"""
    consultation = db.query(Consultation).filter(Consultation.id == consultation_id).first()
    if not consultation:
        raise HTTPException(status_code=404, detail="Consultation not found")
    
    # Update fields
    update_data = consultation_update.dict(exclude_unset=True)
    for key, value in update_data.items():
        if key == "scheduled_date" and value:
            try:
                value = datetime.fromisoformat(value)
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid date format")
        setattr(consultation, key, value)
    
    consultation.updated_at = func.now()
    db.commit()
    db.refresh(consultation)
    
    return consultation


# ============ SEND REMINDER (Manual Trigger) ============
@router.post("/{consultation_id}/send-reminder")
def send_reminder(
    consultation_id: int,
    db: Session = Depends(get_db),
    staff_id: int = Depends(get_current_staff)
):
    """Manually send a reminder email for a consultation"""
    consultation = db.query(Consultation).options(joinedload(Consultation.lead)).filter(
        Consultation.id == consultation_id
    ).first()
    
    if not consultation:
        raise HTTPException(status_code=404, detail="Consultation not found")
    
    lead = consultation.lead
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    
    success, msg = send_consultation_reminder(consultation, lead)
    if success:
        consultation.reminder_sent = 1
        db.commit()
        return {"message": "Reminder sent successfully"}
    else:
        raise HTTPException(status_code=500, detail=f"Failed to send reminder: {msg}")


# ============ AUTO-REMINDER BACKGROUND JOB ============
def send_due_reminders(db: Session):
    """Send reminders for consultations scheduled TODAY"""
    from datetime import datetime
    from sqlalchemy import func
    
    today = datetime.now().date()
    print(f"🔍 DEBUG: Today is {today}")
    
    # Query for consultations
    consultations = db.query(Consultation).options(joinedload(Consultation.lead)).filter(
        func.date(Consultation.scheduled_date) == today,
        Consultation.reminder_sent == 0,
        Consultation.status.in_(["scheduled", "consultation"])
    ).all()
    
    print(f"🔍 DEBUG: Found {len(consultations)} consultations")
    
    sent_count = 0
    for consultation in consultations:
        print(f"🔍 DEBUG: Processing consultation {consultation.id}")
        
        lead = consultation.lead
        if not lead:
            print(f"   ❌ No lead found")
            continue
            
        if not lead.email:
            print(f"   ❌ No email for lead {lead.id}")
            continue
        
        print(f"   ✅ Lead: {lead.name} ({lead.email})")
        
        try:
            # ✅ Call with 2 arguments
            success, msg = send_consultation_reminder(consultation, lead)
            if success:
                sent_count += 1
                print(f"   ✅ Sent reminder for consultation {consultation.id}")
            else:
                print(f"   ❌ Failed: {msg}")
        except Exception as e:
            print(f"   ❌ Error: {e}")
            import traceback
            traceback.print_exc()
    
    print(f"🔍 DEBUG: Total sent: {sent_count}")
    db.commit()
    return sent_count