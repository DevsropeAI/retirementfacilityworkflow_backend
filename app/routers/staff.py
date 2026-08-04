from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from sqlalchemy import func  
from typing import Optional, List
from app.core.database import get_db
from app.models.db_models import Staff
from app.schemas.staff import StaffCreate, StaffUpdate, StaffResponse
from app.core.security import get_password_hash, verify_password, decode_token
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

router = APIRouter()
security = HTTPBearer()

def get_current_staff(token: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)):
    payload = decode_token(token.credentials)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    return payload.get("id")

def get_current_admin(token: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)):
    staff_id = get_current_staff(token, db)
    staff = db.query(Staff).filter(Staff.id == staff_id).first()
    if not staff or staff.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return staff_id

# ============ LIST STAFF ============
@router.get("/", response_model=List[StaffResponse])
def get_staff(
    db: Session = Depends(get_db),
    staff_id: int = Depends(get_current_admin)
):
    """Get all staff members (admin only)"""
    staff = db.query(Staff).order_by(Staff.created_at.desc()).all()
    return staff

# ============ GET STAFF DROPDOWN ============

@router.get("/dropdown")
def get_staff_dropdown(
    db: Session = Depends(get_db),
    staff_id: int = Depends(get_current_staff)
):
    staff = db.query(Staff).filter(Staff.is_active == 1).all()
    return [{"id": s.id, "name": s.name, "email": s.email, "role": s.role} for s in staff]


# ============ GET SINGLE STAFF ============
@router.get("/{staff_id}", response_model=StaffResponse)
def get_staff_by_id(
    staff_id: int,
    db: Session = Depends(get_db),
    admin_id: int = Depends(get_current_admin)
):
    """Get a single staff member (admin only)"""
    staff = db.query(Staff).filter(Staff.id == staff_id).first()
    if not staff:
        raise HTTPException(status_code=404, detail="Staff not found")
    return staff

# ============ CREATE STAFF ============
@router.post("/", response_model=StaffResponse)
def create_staff(
    staff_data: StaffCreate,
    db: Session = Depends(get_db),
    admin_id: int = Depends(get_current_admin)
):
    """Create a new staff member (admin only)"""
    
    # Check if email already exists
    existing = db.query(Staff).filter(Staff.email == staff_data.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Create new staff
    new_staff = Staff(
        email=staff_data.email,
        name=staff_data.name,
        hashed_password=get_password_hash(staff_data.password),
        role=staff_data.role,
        is_active=1
    )
    
    db.add(new_staff)
    db.commit()
    db.refresh(new_staff)
    
    return new_staff

# ============ UPDATE STAFF ============
@router.put("/{staff_id}", response_model=StaffResponse)
def update_staff(
    staff_id: int,
    staff_data: StaffUpdate,
    db: Session = Depends(get_db),
    admin_id: int = Depends(get_current_admin)
):
    """Update a staff member (admin only)"""
    
    staff = db.query(Staff).filter(Staff.id == staff_id).first()
    if not staff:
        raise HTTPException(status_code=404, detail="Staff not found")
    
    # Prevent admin from deactivating themselves
    if staff_id == admin_id and staff_data.is_active == 0:
        raise HTTPException(status_code=400, detail="You cannot deactivate yourself")
    
    update_data = staff_data.dict(exclude_unset=True)
    
    if "password" in update_data and update_data["password"]:
        staff.hashed_password = get_password_hash(update_data["password"])
        del update_data["password"]
    
    for key, value in update_data.items():
        setattr(staff, key, value)
    
    staff.updated_at = func.now()
    db.commit()
    db.refresh(staff)
    
    return staff

# ============ DELETE STAFF ============
@router.delete("/{staff_id}")
def delete_staff(
    staff_id: int,
    db: Session = Depends(get_db),
    admin_id: int = Depends(get_current_admin)
):
    """Delete a staff member (admin only)"""
    
    if staff_id == admin_id:
        raise HTTPException(status_code=400, detail="You cannot delete yourself")
    
    staff = db.query(Staff).filter(Staff.id == staff_id).first()
    if not staff:
        raise HTTPException(status_code=404, detail="Staff not found")
    
    db.delete(staff)
    db.commit()
    
    return {"message": "Staff deleted successfully"}

# @router.get("/dropdown")
# def get_staff_dropdown(
#     db: Session = Depends(get_db),
#     staff_id: int = Depends(get_current_staff)
# ):
#     """Get active staff for dropdown (all authenticated staff can access)"""
#     staff = db.query(Staff).filter(Staff.is_active == 1).all()
#     return [{"id": s.id, "name": s.name, "email": s.email, "role": s.role} for s in staff]

# @router.get("/dropdown")
# def get_staff_dropdown(
#     db: Session = Depends(get_db),
#     credentials: HTTPAuthorizationCredentials = Depends(security)  # ← Get credentials directly
# ):
#     print(f"🔍 Token received: {credentials.credentials[:30]}...")
    
#     payload = decode_token(credentials.credentials)
#     if not payload:
#         print("❌ Invalid token")
#         raise HTTPException(status_code=401, detail="Invalid token")
    
#     staff_id = payload.get("id")
#     print(f"👤 Staff ID: {staff_id}")
    
#     staff = db.query(Staff).filter(Staff.is_active == 1).all()
#     print(f"👥 Found {len(staff)} active staff")
    
#     return [{"id": s.id, "name": s.name, "email": s.email, "role": s.role} for s in staff]