from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class LoanCalculationBase(BaseModel):
    principal: float
    interest_rate: float
    tenure_months: int
    emi: Optional[float] = None
    total_interest: Optional[float] = None
    total_payment: Optional[float] = None

class LoanCalculationCreate(LoanCalculationBase):
    case_id: int

class LoanCalculationResponse(LoanCalculationBase):
    id: int
    case_id: int
    created_at: datetime

    class Config:
        from_attributes = True
