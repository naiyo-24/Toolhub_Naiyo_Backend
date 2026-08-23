from sqlalchemy import Column, Integer, String, Numeric, ForeignKey, DateTime, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from database import Base

class RiskAnalysis(Base):
    __tablename__ = "risk_analyses"

    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, ForeignKey("loan_cases.id"), nullable=False, unique=True, index=True)

    # Core Metrics
    verified_monthly_income = Column(Numeric(15,2), nullable=True)
    existing_emi = Column(Numeric(15,2), nullable=True)
    proposed_emi = Column(Numeric(15,2), nullable=True)
    foir_percentage = Column(Numeric(10,2), nullable=True)
    
    # Risk Score & Decision
    risk_score = Column(Integer, nullable=True) # 0-100
    risk_grade = Column(String, nullable=True) # A, B, C, etc.
    decision = Column(String, nullable=True) # ELIGIBLE, REVIEW, NOT ELIGIBLE
    
    # Structured detailed results (JSON)
    # Stores the Pass/Warning/Fail parameters, Positive/Risk factors, and full explanation
    analysis_details = Column(JSON, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    case = relationship("LoanCase")
