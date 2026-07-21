from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.core.database import get_db
from app.models.db_models import Staff
from app.core.security import verify_password, get_password_hash, create_access_token

router = APIRouter()

class LoginRequest(BaseModel):
    email: str
    password: str

class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    staff_id: int
    name: str
    email: str
    role: str

class RegisterRequest(BaseModel):
    email: str
    name: str
    password: str
    role: str = "staff"

@router.post("/login", response_model=LoginResponse)
def login(request: LoginRequest, db: Session = Depends(get_db)):
    staff = db.query(Staff).filter(Staff.email == request.email).first()
    if not staff:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    if not verify_password(request.password, staff.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    token = create_access_token({"sub": staff.email, "id": staff.id, "role": staff.role})
    
    return LoginResponse(
        access_token=token,
        staff_id=staff.id,
        name=staff.name,
        email=staff.email,
        role=staff.role
    )

@router.post("/register")
def register(request: RegisterRequest, db: Session = Depends(get_db)):
    existing = db.query(Staff).filter(Staff.email == request.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    hashed = get_password_hash(request.password)
    staff = Staff(
        email=request.email,
        name=request.name,
        hashed_password=hashed,
        role=request.role
    )
    db.add(staff)
    db.commit()
    db.refresh(staff)
    
    return {"message": "Staff registered successfully", "id": staff.id}