from sqlalchemy import Column, Integer, String, Numeric, ForeignKey, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from database import Base

class FinancialAnalysis(Base):
    __tablename__ = "financial_analyses"

    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, ForeignKey("loan_cases.id"), nullable=False, index=True)

    total_income = Column(Numeric(15,2), nullable=True)
    total_expense = Column(Numeric(15,2), nullable=True)
    net_cash_flow = Column(Numeric(15,2), nullable=True)

    current_ratio = Column(Numeric(10,4), nullable=True)
    quick_ratio = Column(Numeric(10,4), nullable=True)
    debt_equity_ratio = Column(Numeric(10,4), nullable=True)

    gross_margin = Column(Numeric(10,4), nullable=True)
    net_margin = Column(Numeric(10,4), nullable=True)

    interest_coverage = Column(Numeric(10,4), nullable=True)
    dscr = Column(Numeric(10,4), nullable=True)

    financial_health = Column(String, nullable=True) # EXCELLENT, GOOD, FAIR, POOR
    calculation_version = Column(String, nullable=True, default="v1.0")

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    case = relationship("LoanCase")
