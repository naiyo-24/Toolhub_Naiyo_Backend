from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func
from database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    google_id = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    full_name = Column(String, nullable=True)
    profile_pic = Column(String, nullable=True)
    company_name = Column(String, nullable=True)
    company_logo_url = Column(String, nullable=True)
    company_address = Column(String, nullable=True)
    whatsapp_number = Column(String, nullable=True)
    phone_number = Column(String, nullable=True)
    gst_number = Column(String, nullable=True)
    business_type = Column(String, nullable=True, default="Retailer")
    bank_name = Column(String, nullable=True)
    account_name = Column(String, nullable=True)
    account_number = Column(String, nullable=True)
    ifsc_code = Column(String, nullable=True)
    pricing_mode = Column(String, default="INCLUSIVE") # INCLUSIVE or EXCLUSIVE
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
