from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import auth, leads, dashboard, consultations 
from app.core.database import engine
from app.models.db_models import Base
from app.core.config import settings

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


@app.get("/")
def root():
    return {"message": "Retirees Paradise API is running"}