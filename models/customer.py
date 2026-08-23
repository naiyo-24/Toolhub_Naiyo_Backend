from sqlalchemy import Column, Integer, String, Date, Text, ForeignKey, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from database import Base
from utils.ids import generate_case_number, generate_customer_number

class Customer(Base):
    __tablename__ = "customers"

    id = Column(Integer, primary_key=True, index=True)
    customer_number = Column(String, unique=True, index=True, default=generate_customer_number)
    customer_type = Column(String, nullable=False) # e.g. INDIVIDUAL, BUSINESS

    full_name = Column(String, index=True, nullable=False)
    mobile = Column(String, index=True, nullable=False)
    email = Column(String, nullable=True)

    pan = Column(String, index=True, nullable=True)
    dob = Column(Date, nullable=True)

    occupation = Column(String, nullable=True)
    address = Column(Text, nullable=True)

    legal_name = Column(String, nullable=True)
    business_name = Column(String, index=True, nullable=True)
    business_type = Column(String, nullable=True)

    gstin = Column(String, index=True, nullable=True)
    udyam_number = Column(String, index=True, nullable=True)

    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    creator = relationship("User")
