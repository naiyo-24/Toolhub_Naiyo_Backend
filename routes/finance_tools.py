from fastapi import APIRouter, HTTPException
from schemas.finance_tools import (
    EMICalculatorRequest, SIPCalculatorRequest, LoanCalculatorRequest, 
    TaxCalculatorRequest, GSTCalculatorRequest, CurrencyConverterRequest,
    SavingsPlannerRequest, BudgetPlannerRequest, ExpenseTrackerRequest,
    InvestmentCalculatorRequest, CompoundInterestRequest, SalaryCalculatorRequest
)

router = APIRouter()

@router.post("/emi-calculator")
def emi_calculator(req: EMICalculatorRequest):
    p = req.principal
    r = req.annual_interest_rate / 12 / 100
    n = req.tenure_months
    
    if r == 0:
        emi = p / n
        total_interest = 0
    else:
        emi = p * r * ((1 + r)**n) / (((1 + r)**n) - 1)
        total_interest = (emi * n) - p
        
    return {
        "monthly_emi": round(emi, 2),
        "total_interest": round(total_interest, 2),
        "total_amount": round(p + total_interest, 2)
    }

@router.post("/sip-calculator")
def sip_calculator(req: SIPCalculatorRequest):
    p = req.monthly_investment
    r = req.expected_annual_return / 12 / 100
    n = req.time_period_years * 12
    
    if r == 0:
        expected_amount = p * n
    else:
        expected_amount = p * (((1 + r)**n - 1) / r) * (1 + r)
        
    invested_amount = p * n
    wealth_gained = expected_amount - invested_amount
    
    return {
        "invested_amount": round(invested_amount, 2),
        "wealth_gained": round(wealth_gained, 2),
        "expected_amount": round(expected_amount, 2)
    }

@router.post("/loan-calculator")
def loan_calculator(req: LoanCalculatorRequest):
    # Standard loan calculation
    p = req.principal
    r = req.annual_interest_rate / 12 / 100
    n = req.tenure_months
    
    if r == 0:
        emi = p / n
        total_interest = 0
    else:
        emi = p * r * ((1 + r)**n) / (((1 + r)**n) - 1)
        total_interest = (emi * n) - p
        
    return {
        "monthly_payment": round(emi, 2),
        "total_interest": round(total_interest, 2),
        "total_payment": round(p + total_interest, 2)
    }

@router.post("/tax-calculator")
def tax_calculator(req: TaxCalculatorRequest):
    # Indian New Tax Regime (FY 2024-25)
    # Income upto 3L: Nil
    # 3L - 6L: 5%
    # 6L - 9L: 10%
    # 9L - 12L: 15%
    # 12L - 15L: 20%
    # Above 15L: 30%
    # Rebate under 87A up to 7L income (Tax becomes 0)
    
    income = req.annual_income
    
    if income <= 700000:
        return {"taxable_income": income, "tax_liability": 0, "effective_tax_rate": 0}
        
    tax = 0
    if income > 1500000:
        tax += (income - 1500000) * 0.30
        income = 1500000
    if income > 1200000:
        tax += (income - 1200000) * 0.20
        income = 1200000
    if income > 900000:
        tax += (income - 900000) * 0.15
        income = 900000
    if income > 600000:
        tax += (income - 600000) * 0.10
        income = 600000
    if income > 300000:
        tax += (income - 300000) * 0.05
        
    # Health and Education Cess @ 4%
    cess = tax * 0.04
    total_tax = tax + cess
    
    return {
        "taxable_income": req.annual_income,
        "tax_liability": round(total_tax, 2),
        "effective_tax_rate": round((total_tax / req.annual_income) * 100, 2)
    }

@router.post("/gst-calculator")
def gst_calculator(req: GSTCalculatorRequest):
    if req.is_inclusive:
        base_amount = req.amount / (1 + (req.gst_rate / 100))
        gst_amount = req.amount - base_amount
        total_amount = req.amount
    else:
        base_amount = req.amount
        gst_amount = req.amount * (req.gst_rate / 100)
        total_amount = req.amount + gst_amount
        
    cgst = gst_amount / 2
    sgst = gst_amount / 2
    
    return {
        "base_amount": round(base_amount, 2),
        "gst_amount": round(gst_amount, 2),
        "cgst": round(cgst, 2),
        "sgst": round(sgst, 2),
        "total_amount": round(total_amount, 2)
    }

from utils import calculators
from schemas.daily_utility import CurrencyCode

@router.post("/currency-converter")
async def currency_converter(req: CurrencyConverterRequest):
    try:
        converted = calculators.convert_currency(req.amount, req.from_currency.value, req.to_currency.value)
        return {
            "converted_amount": converted,
            "exchange_rate": converted / req.amount if req.amount != 0 else 0,
            "date": "Latest"
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/savings-planner")
def savings_planner(req: SavingsPlannerRequest):
    f = req.goal_amount
    r = req.expected_annual_return / 12 / 100
    n = req.time_period_years * 12
    
    if r == 0:
        monthly = f / n
    else:
        monthly = f / ((((1 + r)**n - 1) / r) * (1 + r))
        
    return {
        "monthly_savings_required": round(monthly, 2),
        "total_investment": round(monthly * n, 2),
        "wealth_gained": round(f - (monthly * n), 2)
    }

@router.post("/budget-planner")
def budget_planner(req: BudgetPlannerRequest):
    income = req.monthly_income
    
    if req.needs_percentage + req.wants_percentage + req.savings_percentage != 100:
        raise HTTPException(status_code=400, detail="Percentages must add up to exactly 100.")
        
    needs = income * (req.needs_percentage / 100)
    wants = income * (req.wants_percentage / 100)
    savings = income * (req.savings_percentage / 100)
    
    return {
        "monthly_income": income,
        "rule_used": f"{int(req.needs_percentage)}/{int(req.wants_percentage)}/{int(req.savings_percentage)}",
        "allocation": {
            "needs": {
                "total": round(needs, 2),
                "suggested_breakdown": {
                    "housing_rent": round(needs * 0.5, 2),
                    "groceries_food": round(needs * 0.25, 2),
                    "utilities_bills": round(needs * 0.15, 2),
                    "transportation": round(needs * 0.10, 2)
                }
            },
            "wants": {
                "total": round(wants, 2),
                "suggested_breakdown": {
                    "dining_out": round(wants * 0.4, 2),
                    "entertainment": round(wants * 0.3, 2),
                    "shopping": round(wants * 0.3, 2)
                }
            },
            "savings_investments": {
                "total": round(savings, 2),
                "suggested_breakdown": {
                    "emergency_fund": round(savings * 0.3, 2),
                    "investments_mutual_funds": round(savings * 0.5, 2),
                    "retirement": round(savings * 0.2, 2)
                }
            }
        }
    }

@router.post("/expense-tracker")
def expense_tracker(req: ExpenseTrackerRequest):
    total_spent = sum(item.amount for item in req.expenses)
    
    categories = {}
    for item in req.expenses:
        cat = item.category.value
        categories[cat] = categories.get(cat, 0) + item.amount
        
    # Calculate percentage for each category
    breakdown = []
    highest_category = {"category": None, "amount": 0}
    
    for cat, amount in categories.items():
        percentage = (amount / total_spent) * 100 if total_spent > 0 else 0
        breakdown.append({
            "category": cat,
            "total_amount": round(amount, 2),
            "percentage_of_total": round(percentage, 2)
        })
        
        if amount > highest_category["amount"]:
            highest_category = {"category": cat, "amount": round(amount, 2)}
            
    remaining_budget = req.monthly_budget - total_spent
    budget_status = "Under Budget"
    if remaining_budget < 0:
        budget_status = "Over Budget"
    elif remaining_budget == 0:
        budget_status = "Exactly on Budget"
        
    return {
        "monthly_budget": req.monthly_budget,
        "total_spent": round(total_spent, 2),
        "remaining_balance": round(remaining_budget, 2),
        "budget_status": budget_status,
        "highest_expense_category": highest_category["category"],
        "category_breakdown": sorted(breakdown, key=lambda x: x["total_amount"], reverse=True)
    }

@router.post("/investment-calculator")
def investment_calculator(req: InvestmentCalculatorRequest):
    p = req.lumpsum_amount
    r = req.expected_annual_return / 100
    t = req.time_period_years
    
    future_value = p * ((1 + r)**t)
    wealth_gained = future_value - p
    
    return {
        "invested_amount": p,
        "wealth_gained": round(wealth_gained, 2),
        "expected_amount": round(future_value, 2)
    }

@router.post("/compound-interest")
def compound_interest(req: CompoundInterestRequest):
    p = req.principal
    r = req.annual_interest_rate / 100
    t = req.time_period_years
    n = req.compound_frequency
    
    amount = p * ((1 + (r / n)) ** (n * t))
    interest = amount - p
    
    return {
        "principal": p,
        "total_interest": round(interest, 2),
        "total_amount": round(amount, 2)
    }

@router.post("/salary-calculator")
def salary_calculator(req: SalaryCalculatorRequest):
    # Simplistic estimation
    basic = req.ctc * (req.basic_percentage / 100)
    hra = basic * (req.hra_percentage / 100)
    pf_employee = basic * 0.12 # 12% of basic
    
    # Taxable Income = CTC - Standard Deduction - PF
    taxable = req.ctc - req.standard_deduction - pf_employee
    
    # Calculate Tax (using same New Regime logic)
    income = taxable
    tax = 0
    if income > 700000:
        if income > 1500000:
            tax += (income - 1500000) * 0.30
            income = 1500000
        if income > 1200000:
            tax += (income - 1200000) * 0.20
            income = 1200000
        if income > 900000:
            tax += (income - 900000) * 0.15
            income = 900000
        if income > 600000:
            tax += (income - 600000) * 0.10
            income = 600000
        if income > 300000:
            tax += (income - 300000) * 0.05
    cess = tax * 0.04
    yearly_tax = tax + cess
    
    yearly_take_home = req.ctc - pf_employee - yearly_tax
    monthly_take_home = yearly_take_home / 12
    
    return {
        "ctc": req.ctc,
        "basic": round(basic, 2),
        "hra": round(hra, 2),
        "yearly_pf_deduction": round(pf_employee, 2),
        "yearly_tax_deduction": round(yearly_tax, 2),
        "yearly_take_home": round(yearly_take_home, 2),
        "monthly_take_home": round(monthly_take_home, 2)
    }
