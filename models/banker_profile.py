from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from database import Base

class BankerProfile(Base):
    __tablename__ = "banker_profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, index=True)
    mobile = Column(String, nullable=True)
    role = Column(String, nullable=True)
    designation = Column(String, nullable=True)
    employee_id = Column(String, nullable=True)
    experience_years = Column(Integer, nullable=True)
    org_type = Column(String, nullable=True)
    org_name = Column(String, nullable=True)
    branch_name = Column(String, nullable=True)
    city = Column(String, nullable=True)
    state_region = Column(String, nullable=True)
    loan_types = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    user = relationship("User", backref="banker_profile")

class BankerLoanPreference(Base):
    __tablename__ = "banker_loan_preferences"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    loan_type = Column(String, nullable=False) # e.g., BUSINESS, MSME, PERSONAL
