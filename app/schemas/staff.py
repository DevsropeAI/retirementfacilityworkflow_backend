from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class StaffCreate(BaseModel):
    email: str  
    name: str
    password: str
    role: str = "staff" 

class StaffUpdate(BaseModel):
    name: Optional[str] = None
    role: Optional[str] = None
    is_active: Optional[int] = None
    password: Optional[str] = None

class StaffResponse(BaseModel):
    id: int
    email: str
    name: str
    role: str
    is_active: int
    created_at: datetime
    updated_at: Optional[datetime]
    
    class Config:
        from_attributes = True