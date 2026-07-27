import hashlib
import uuid
import time
from sqlalchemy.orm import Session
from app.models.db_models import Lead

def generate_application_token(lead_id: int) -> str:
    """Generate a unique token for a lead"""
    token_string = f"{lead_id}-{time.time()}-{uuid.uuid4()}"
    return hashlib.sha256(token_string.encode()).hexdigest()[:32]

def get_lead_by_token(db: Session, token: str):
    """Get a lead by their application token"""
    return db.query(Lead).filter(Lead.application_token == token).first()

def generate_application_link(token: str) -> str:
    """Generate the full application link"""
    return f"http://localhost:3000/apply/{token}"