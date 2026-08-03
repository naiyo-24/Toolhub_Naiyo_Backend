from pydantic import BaseModel, Field
from typing import List, Optional

class EMICalculatorRequest(BaseModel):
    principal: float = Field(..., description="Loan amount")
    annual_interest_rate: float = Field(..., description="Annual interest rate in percentage")
    tenure_months: int = Field(..., description="Loan tenure in months")

class SIPCalculatorRequest(BaseModel):
    monthly_investment: float = Field(..., description="Amount invested per month")
    expected_annual_return: float = Field(..., description="Expected annual return rate in percentage")
    time_period_years: int = Field(..., description="Investment duration in years")

class LoanCalculatorRequest(BaseModel):
    principal: float = Field(..., description="Loan amount")
    annual_interest_rate: float = Field(..., description="Annual interest rate in percentage")
    tenure_months: int = Field(..., description="Loan tenure in months")

class TaxCalculatorRequest(BaseModel):
    annual_income: float = Field(..., description="Total annual income in INR")
    
class GSTCalculatorRequest(BaseModel):
    amount: float = Field(..., description="Base amount")
    gst_rate: float = Field(..., description="GST percentage (e.g., 5, 12, 18, 28)")
    is_inclusive: bool = Field(False, description="True if the amount already includes GST")

from schemas.daily_utility import CurrencyCode

class CurrencyConverterRequest(BaseModel):
    amount: float = Field(..., description="Amount to convert")
    from_currency: CurrencyCode = Field(..., description="Base currency code (e.g., USD, INR)")
    to_currency: CurrencyCode = Field(..., description="Target currency code (e.g., EUR, GBP)")

class SavingsPlannerRequest(BaseModel):
    goal_amount: float = Field(..., description="Target savings amount")
    expected_annual_return: float = Field(..., description="Expected annual return rate in percentage")
    time_period_years: int = Field(..., description="Time to reach goal in years")

class BudgetPlannerRequest(BaseModel):
    monthly_income: float = Field(..., description="Total monthly income")
    needs_percentage: float = Field(50.0, description="Percentage for Needs (e.g., 50)")
    wants_percentage: float = Field(30.0, description="Percentage for Wants (e.g., 30)")
    savings_percentage: float = Field(20.0, description="Percentage for Savings (e.g., 20)")

from enum import Enum

class ExpenseCategory(str, Enum):
    HOUSING = "Housing"
    FOOD = "Food & Dining"
    TRANSPORTATION = "Transportation"
    UTILITIES = "Utilities & Bills"
    ENTERTAINMENT = "Entertainment"
    HEALTHCARE = "Healthcare"
    SHOPPING = "Shopping"
    TRAVEL = "Travel"
    EDUCATION = "Education"
    OTHER = "Other"

class ExpenseItem(BaseModel):
    category: ExpenseCategory = Field(..., description="Category of the expense")
    amount: float = Field(..., description="Cost of the expense")
    description: Optional[str] = Field(None, description="Optional note about the expense")
    date: Optional[str] = Field(None, description="Optional date of the expense (YYYY-MM-DD)")

class ExpenseTrackerRequest(BaseModel):
    monthly_budget: float = Field(..., description="Your total budget for the month")
    expenses: List[ExpenseItem] = Field(..., description="List of all expenses")

class InvestmentCalculatorRequest(BaseModel):
    lumpsum_amount: float = Field(..., description="Initial lumpsum investment")
    expected_annual_return: float = Field(..., description="Expected annual return rate in percentage")
    time_period_years: int = Field(..., description="Investment duration in years")

class CompoundInterestRequest(BaseModel):
    principal: float = Field(..., description="Initial principal amount")
    annual_interest_rate: float = Field(..., description="Annual interest rate in percentage")
    time_period_years: int = Field(..., description="Time period in years")
    compound_frequency: int = Field(12, description="Times interest is compounded per year (e.g., 12 for monthly)")

class SalaryCalculatorRequest(BaseModel):
    ctc: float = Field(..., description="Cost to Company (Annual)")
    basic_percentage: float = Field(50, description="Basic salary as a percentage of CTC")
    hra_percentage: float = Field(50, description="HRA as a percentage of Basic Salary")
    standard_deduction: float = Field(50000, description="Standard deduction for salaried employees")
