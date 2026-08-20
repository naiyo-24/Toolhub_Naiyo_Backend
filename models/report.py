from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from database import Base

class Report(Base):
    __tablename__ = "reports"

    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, ForeignKey("loan_cases.id"), nullable=False, index=True)

    report_type = Column(String, nullable=False) # e.g. CREDIT_MEMO, RISK_ASSESSMENT
    file_path = Column(String, nullable=True) # If generated as PDF
    status = Column(String, default="GENERATED")

    generated_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    case = relationship("LoanCase")
    generator = relationship("User")
