from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from db import engine, Base
from routes import tools, daily_utility, internet_tools, file_tools, ai_tools, student_tools
import models.tool  # Import models so Base.metadata knows about them
import models.user
import models.business
import models.forms
import os

from sqlalchemy import text

# Run automatic migrations for new columns
try:
    with engine.begin() as conn:
        conn.execute(text("ALTER TABLE products ADD COLUMN image_url VARCHAR;"))
except Exception:
    pass

try:
    with engine.begin() as conn:
        conn.execute(text("UPDATE products SET product_type = 'Raw Material' WHERE name IN ('DELL MONITOR 16INCH', 'Tap');"))
except Exception:
    pass

try:
    with engine.begin() as conn:
        conn.execute(text("ALTER TABLE invoice_records ADD COLUMN pdf_url VARCHAR;"))
except Exception:
    pass

try:
    with engine.begin() as conn:
        conn.execute(text("ALTER TABLE users ADD COLUMN company_logo_url VARCHAR;"))
except Exception:
    pass

try:
    with engine.begin() as conn:
        conn.execute(text("ALTER TABLE users ADD COLUMN pricing_mode VARCHAR DEFAULT 'INCLUSIVE';"))
except Exception:
    pass

try:
    with engine.begin() as conn:
        conn.execute(text("ALTER TABLE retailer_inventory ADD COLUMN batch_number VARCHAR;"))
except Exception:
    pass
    
try:
    with engine.begin() as conn:
        conn.execute(text("ALTER TABLE retailer_inventory ADD COLUMN expiry_date DATE;"))
except Exception:
    pass

try:
    with engine.begin() as conn:
        conn.execute(text("ALTER TABLE retailer_inventory ADD COLUMN reminder_stock INTEGER DEFAULT 0;"))
except Exception:
    pass

try:
    with engine.begin() as conn:
        conn.execute(text("ALTER TABLE products ADD COLUMN gst_id INTEGER REFERENCES gst_master(id);"))
except Exception:
    pass

# Create database tables (can be removed if relying strictly on alembic)
Base.metadata.create_all(bind=engine)

# Seed GST Master
from sqlalchemy.orm import Session
from db import SessionLocal
from models.business import GSTMaster

def seed_gst_master():
    db = SessionLocal()
    try:
        default_slabs = [
            {"rate": 0.0, "cgst": 0.0, "sgst": 0.0, "igst": 0.0},
            {"rate": 5.0, "cgst": 2.5, "sgst": 2.5, "igst": 5.0},
            {"rate": 12.0, "cgst": 6.0, "sgst": 6.0, "igst": 12.0},
            {"rate": 18.0, "cgst": 9.0, "sgst": 9.0, "igst": 18.0},
            {"rate": 28.0, "cgst": 14.0, "sgst": 14.0, "igst": 28.0},
        ]
        for slab in default_slabs:
            exists = db.query(GSTMaster).filter(GSTMaster.gst_rate == slab["rate"]).first()
            if not exists:
                new_slab = GSTMaster(
                    gst_rate=slab["rate"],
                    cgst=slab["cgst"],
                    sgst=slab["sgst"],
                    igst=slab["igst"]
                )
                db.add(new_slab)
        db.commit()
    finally:
        db.close()

seed_gst_master()

os.makedirs("uploads", exist_ok=True)

app = FastAPI(
    title="Toolhub Naiyo API",
    description="Backend API for Toolhub Naiyo Mobile Application",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

app.include_router(tools.router)
app.include_router(daily_utility.router)
app.include_router(internet_tools.router)
app.include_router(file_tools.router)
app.include_router(ai_tools.router)
from routes.docuforge import router as docuforge_router
from routes.finance_tools import router as finance_tools_router
from routes.business_tools import router as business_tools_router
from routes.social_tools import router as social_tools_router
from routes.health_tools import router as health_tools_router
from routes.productivity_tools import router as productivity_tools_router
from routes.travel_tools import router as travel_tools_router
from routes.form_tools import router as form_tools_router
from routes.auth import router as auth_router

app.include_router(student_tools.router)
app.include_router(docuforge_router, prefix="/docuforge", tags=["DocuForge"])
app.include_router(finance_tools_router, prefix="/finance-tools", tags=["Finance Tools"])
app.include_router(business_tools_router, prefix="/business-tools", tags=["Business Toolkit"])
app.include_router(social_tools_router, prefix="/social-tools", tags=["Social Tools"])
app.include_router(health_tools_router, prefix="/health-tools", tags=["Health Tools"])
app.include_router(productivity_tools_router, prefix="/productivity-tools", tags=["Productivity Tools"])
app.include_router(travel_tools_router, prefix="/travel-tools", tags=["Travel Tools"])
app.include_router(form_tools_router, prefix="/form-builder", tags=["Form Builder"])
app.include_router(auth_router, prefix="/auth", tags=["Authentication"])

@app.get("/")
def read_root():
    return {"message": "Welcome to the Toolhub Naiyo API!"}
