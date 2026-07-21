from app.core.database import SessionLocal
from app.models.db_models import Staff
from app.core.security import get_password_hash

db = SessionLocal()

# Delete existing staff
staff = db.query(Staff).filter(Staff.email == "admin@retireesparadise.com").first()
if staff:
    db.delete(staff)
    db.commit()
    print("✅ Removed existing staff")

# Create new staff with SHA256
staff = Staff(
    email="admin@retireesparadise.com",
    name="Admin User",
    hashed_password=get_password_hash("admin123"),
    role="admin",
    is_active=1
)
db.add(staff)
db.commit()
db.refresh(staff)
print("✅ Staff created successfully!")
print(f"   Email: {staff.email}")
print(f"   Password: admin123")
db.close()