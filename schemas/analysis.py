from pydantic import BaseModel
from typing import Optional
from datetime import date, datetime

class BankStatementBase(BaseModel):
    bank_name: Optional[str] = None
    account_number_masked: Optional[str] = None
    statement_start: Optional[date] = None
    statement_end: Optional[date] = None
    total_credits: Optional[float] = None
    total_debits: Optional[float] = None
    average_balance: Optional[float] = None
    highest_balance: Optional[float] = None
    lowest_balance: Optional[float] = None
    total_cash_deposits: Optional[float] = None
    total_cash_withdrawals: Optional[float] = None

class BankStatementCreate(BankStatementBase):
    case_id: int
    document_id: Optional[int] = None

class BankStatementUpdate(BankStatementBase):
    pass

class BankStatementResponse(BankStatementBase):
    id: int
    case_id: int
    document_id: Optional[int] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class FinancialAnalysisBase(BaseModel):
    total_income: Optional[float] = None
    total_expense: Optional[float] = None
    net_cash_flow: Optional[float] = None
    current_ratio: Optional[float] = None
    quick_ratio: Optional[float] = None
    debt_equity_ratio: Optional[float] = None
    gross_margin: Optional[float] = None
    net_margin: Optional[float] = None
    interest_coverage: Optional[float] = None
    dscr: Optional[float] = None
    financial_health: Optional[str] = None

class FinancialAnalysisCreate(FinancialAnalysisBase):
    case_id: int
    calculation_version: Optional[str] = "v1.0"

class FinancialAnalysisUpdate(FinancialAnalysisBase):
    pass

class FinancialAnalysisResponse(FinancialAnalysisBase):
    id: int
    case_id: int
    calculation_version: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True
