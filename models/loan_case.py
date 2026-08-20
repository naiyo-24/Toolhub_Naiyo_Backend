from sqlalchemy import Column, Integer, String, Numeric, ForeignKey, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from database import Base
from utils.ids import generate_case_number

class LoanCase(Base):
    __tablename__ = "loan_cases"

    id = Column(Integer, primary_key=True, index=True)
    case_number = Column(String, unique=True, index=True, default=generate_case_number)
    
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False, index=True)
    banker_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=True, index=True)

    loan_type = Column(String, nullable=False)
    loan_purpose = Column(String, nullable=True)

    requested_amount = Column(Numeric(15,2), nullable=True)
    tenure_months = Column(Integer, nullable=True)
    interest_rate = Column(Numeric(5,2), nullable=True)

    monthly_income = Column(Numeric(15,2), nullable=True)
    other_income = Column(Numeric(15,2), nullable=True)
    existing_emi = Column(Numeric(15,2), nullable=True)
    existing_liabilities = Column(Numeric(15,2), nullable=True)

    status = Column(String, default="DRAFT", index=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    customer = relationship("Customer")
    banker = relationship("User")
    organization = relationship("Organization")

    @property
    def customer_name(self) -> str:
        return self.customer.full_name if self.customer else "Unknown Customer"
