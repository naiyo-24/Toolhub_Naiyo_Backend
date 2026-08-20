from sqlalchemy import Column, Integer, Numeric, ForeignKey, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from database import Base

class LoanCalculation(Base):
    __tablename__ = "loan_calculations"

    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, ForeignKey("loan_cases.id"), nullable=False, index=True)

    principal = Column(Numeric(15,2), nullable=False)
    interest_rate = Column(Numeric(5,2), nullable=False)
    tenure_months = Column(Integer, nullable=False)

    emi = Column(Numeric(15,2), nullable=True)
    total_interest = Column(Numeric(15,2), nullable=True)
    total_payment = Column(Numeric(15,2), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    case = relationship("LoanCase")
