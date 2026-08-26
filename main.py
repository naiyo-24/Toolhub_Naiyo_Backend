from fastapi.responses import PlainTextResponse
from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import io
from PIL import Image

from database import engine, Base
from routes import tools, daily_utility, internet_tools, file_tools, ai_tools, student_tools
import models.tool  # Import models so Base.metadata knows about them
import models.user
import models.business
import models.forms
import models.contact
import models.organization
import models.customer
import models.loan_case
import models.bank_statement
import models.document
import models.ocr_result
import models.financial_analysis
import models.risk_analysis
import models.report
import models.task
import models.verification
import os

from sqlalchemy import text
from logger_setup import setup_logger, LoguruMiddleware

# Initialize custom logger
logger = setup_logger()


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

try:
    with engine.begin() as conn:
        conn.execute(text("ALTER TABLE banker_profiles ADD COLUMN org_type VARCHAR;"))
        conn.execute(text("ALTER TABLE banker_profiles ADD COLUMN org_name VARCHAR;"))
        conn.execute(text("ALTER TABLE banker_profiles ADD COLUMN branch_name VARCHAR;"))
        conn.execute(text("ALTER TABLE banker_profiles ADD COLUMN city VARCHAR;"))
        conn.execute(text("ALTER TABLE banker_profiles ADD COLUMN state_region VARCHAR;"))
        conn.execute(text("ALTER TABLE banker_profiles ADD COLUMN loan_types JSON;"))
except Exception:
    pass

# Create database tables (can be removed if relying strictly on alembic)
Base.metadata.create_all(bind=engine)

# Seed GST Master
from sqlalchemy.orm import Session
from database import SessionLocal
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

# Add custom logger middleware
app.add_middleware(LoguruMiddleware)


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
from routes.contact import router as contact_router
from routes.banker import router as banker_router
from routes.organizations import router as organizations_router
from routes.customers import router as customers_router
from routes.cases import router as cases_router
from routes.documents import router as documents_router
from routes.ocr import router as ocr_router
from routes.verification import router as verification_router
from routes.analysis import router as analysis_router
from routes.calculations import router as calculations_router
from routes.tasks import router as tasks_router
from routes.timeline import router as timeline_router
from routes.reports import router as reports_router
from routes.search import router as search_router

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
app.include_router(contact_router, prefix="/contact", tags=["Contact"])
app.include_router(banker_router, prefix="/banker", tags=["Banker Onboarding"])
app.include_router(organizations_router, prefix="/organizations", tags=["Organizations"])
app.include_router(customers_router, prefix="/customers", tags=["Customers"])
app.include_router(cases_router, prefix="/cases", tags=["Loan Cases"])
app.include_router(documents_router, prefix="/documents", tags=["Documents"])
app.include_router(ocr_router, prefix="/ocr", tags=["OCR"])
app.include_router(verification_router, prefix="/verification", tags=["Verification"])
app.include_router(analysis_router, prefix="/analysis", tags=["Financial Analysis"])
app.include_router(calculations_router, prefix="/calculations", tags=["Loan Calculations"])
app.include_router(tasks_router, prefix="/tasks", tags=["Tasks"])
app.include_router(timeline_router, prefix="/timeline", tags=["Timeline"])
app.include_router(reports_router, prefix="/reports", tags=["Reports"])
app.include_router(search_router, prefix="/search", tags=["Search"])

@app.post("/extract-text", tags=["OCR"])
async def extract_text(file: UploadFile = File(...)):
    import re
    import pytesseract
    from pdf2image import convert_from_bytes
    from PIL import Image
    
    file_bytes = await file.read()
    extracted_text = ""
    
    if file.filename.lower().endswith('.pdf'):
        # Convert PDF to images
        try:
            images = convert_from_bytes(file_bytes, first_page=1, last_page=1)
            for img in images:
                text = pytesseract.image_to_string(img)
                extracted_text += text + "\n"
        except Exception as e:
            return {"error": f"Failed to process PDF: {str(e)}"}
    else:
        # Run PyTesseract on image
        try:
            image = Image.open(io.BytesIO(file_bytes))
            extracted_text = pytesseract.image_to_string(image)
        except Exception as e:
            return {"error": f"Failed to process Image: {str(e)}"}
            
    # Extract structured data using basic Regex
    pan_match = re.search(r'\b[A-Z]{5}[0-9]{4}[A-Z]{1}\b', extracted_text)
    pan = pan_match.group(0) if pan_match else None
    
    aadhaar_match = re.search(r'\b\d{4}\s?\d{4}\s?\d{4}\b', extracted_text)
    aadhaar = aadhaar_match.group(0) if aadhaar_match else None
    
    dob_match = re.search(r'\b(\d{2}[/-]\d{2}[/-]\d{4})\b', extracted_text)
    dob = dob_match.group(1) if dob_match else None
    
    # 15-digit GSTIN (e.g. 22AAAAA0000A1Z5)
    gst_match = re.search(r'\b[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}\b', extracted_text)
    gst_number = gst_match.group(0) if gst_match else None
    
    return {
        "text": extracted_text.strip(),
        "pan": pan,
        "aadhaar": aadhaar,
        "dob": dob,
        "gst_number": gst_number
    }


@app.get("/")
def read_root():
    return {"message": "Welcome to the Toolhub Naiyo API!"}

@app.get("/ads.txt", response_class=PlainTextResponse)
def get_ads_txt():
    return "google.com, pub-8699813078861252, DIRECT, f08c47fec0942fa0"

@app.get("/app-ads.txt", response_class=PlainTextResponse)
def get_app_ads_txt():
    return "google.com, pub-8699813078861252, DIRECT, f08c47fec0942fa0"
