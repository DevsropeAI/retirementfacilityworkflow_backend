from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from app.core.database import get_db
from app.models.db_models import Lead, LeadStatus
from app.core.security import decode_token
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from datetime import datetime, timedelta
from typing import Optional

router = APIRouter()
security = HTTPBearer()

def get_current_staff(token: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)):
    payload = decode_token(token.credentials)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    return payload.get("id")

@router.get("/stats")
def get_dashboard_stats(
    db: Session = Depends(get_db),
    staff_id: int = Depends(get_current_staff)
):
    """Get all dashboard statistics"""
    
    # Total Leads
    total_leads = db.query(Lead).count()
    
    # Qualified Leads by score
    hot_leads = db.query(Lead).filter(Lead.qualification_score == "Hot").count()
    warm_leads = db.query(Lead).filter(Lead.qualification_score == "Warm").count()
    cold_leads = db.query(Lead).filter(Lead.qualification_score == "Cold").count()
    
    # Leads by status
    consultation_leads = db.query(Lead).filter(Lead.status == LeadStatus.CONSULTATION).count()
    application_leads = db.query(Lead).filter(Lead.status == LeadStatus.APPLICATION).count()
    approved_leads = db.query(Lead).filter(Lead.status == LeadStatus.APPROVED).count()
    enrolled_leads = db.query(Lead).filter(Lead.status == LeadStatus.ENROLLED).count()
    
    # Recent Leads (last 5)
    recent_leads = db.query(Lead).order_by(Lead.created_at.desc()).limit(5).all()
    
    # Lead growth (last 30 days vs previous 30 days)
    today = datetime.now()
    last_30_days = today - timedelta(days=30)
    previous_30_days = today - timedelta(days=60)
    
    current_period = db.query(Lead).filter(Lead.created_at >= last_30_days).count()
    previous_period = db.query(Lead).filter(
        and_(
            Lead.created_at >= previous_30_days,
            Lead.created_at < last_30_days
        )
    ).count()
    
    growth = 0
    if previous_period > 0:
        growth = ((current_period - previous_period) / previous_period) * 100
    elif current_period > 0:
        growth = 100
    
    # Format recent leads
    recent_leads_data = []
    for lead in recent_leads:
        recent_leads_data.append({
            "id": lead.id,
            "name": lead.name,
            "email": lead.email,
            "status": lead.status.value if lead.status else "new",
            "qualification_score": lead.qualification_score,
            "created_at": lead.created_at.isoformat() if lead.created_at else None
        })
    
    return {
        "total_leads": total_leads,
        "qualified_leads": {
            "hot": hot_leads,
            "warm": warm_leads,
            "cold": cold_leads
        },
        "status_counts": {
            "consultation": consultation_leads,
            "application": application_leads,
            "approved": approved_leads,
            "enrolled": enrolled_leads
        },
        "recent_leads": recent_leads_data,
        "growth": {
            "current_period": current_period,
            "previous_period": previous_period,
            "percentage": round(growth, 1)
        }
    }