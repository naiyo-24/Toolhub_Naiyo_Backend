from pydantic import BaseModel, model_validator
from typing import Optional

class LoanCaseBase(BaseModel):
    customer_id: int
    organization_id: Optional[int] = None
    loan_type: str
    loan_purpose: Optional[str] = None
    requested_amount: Optional[float] = None
    tenure_months: Optional[int] = None
    interest_rate: Optional[float] = None
    monthly_income: Optional[float] = None
    other_income: Optional[float] = None
    existing_emi: Optional[float] = None
    existing_liabilities: Optional[float] = None
    status: Optional[str] = "DRAFT"

    @model_validator(mode='before')
    @classmethod
    def map_fields(cls, values):
        if not isinstance(values, dict):
            return values
        if 'amount' in values and 'requested_amount' not in values:
            try:
                values['requested_amount'] = float(values['amount'])
            except (ValueError, TypeError):
                pass
        return values

class LoanCaseCreate(LoanCaseBase):
    pass

class LoanCaseUpdate(BaseModel):
    loan_type: Optional[str] = None
    loan_purpose: Optional[str] = None
    requested_amount: Optional[float] = None
    tenure_months: Optional[int] = None
    interest_rate: Optional[float] = None
    monthly_income: Optional[float] = None
    other_income: Optional[float] = None
    existing_emi: Optional[float] = None
    existing_liabilities: Optional[float] = None
    status: Optional[str] = None

class LoanCaseResponse(LoanCaseBase):
    id: int
    case_number: str
    banker_id: int
    customer_name: Optional[str] = None
    amount: Optional[float] = None

    @model_validator(mode='after')
    def set_amount(self):
        if self.requested_amount is not None:
            self.amount = self.requested_amount
        return self

    class Config:
        from_attributes = True
