from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import auth, leads, dashboard, consultations, notifications, applications
from app.core.database import engine
from app.models.db_models import Base
from app.core.config import settings
from app.core.scheduler import start_scheduler, shutdown_scheduler  
import atexit  

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Retirees Paradise CRM API", version="1.0.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(leads.router, prefix="/api/leads", tags=["leads"])
app.include_router(dashboard.router, prefix="/api/dashboard", tags=["dashboard"])  
app.include_router(consultations.router, prefix="/api/consultations", tags=["consultations"])
app.include_router(notifications.router, prefix="/api/notifications", tags=["notifications"])
app.include_router(applications.router, prefix="/api/applications", tags=["applications"])

@app.get("/")
def root():
    return {"message": "Retirees Paradise API is running"}

# ============ START SCHEDULER ============
@app.on_event("startup")
def startup_event():
    """Start the scheduler when the app starts"""
    start_scheduler()

@app.on_event("shutdown")
def shutdown_event():
    """Shutdown the scheduler when the app stops"""
    shutdown_scheduler()

# Also register for clean exit
atexit.register(shutdown_scheduler)