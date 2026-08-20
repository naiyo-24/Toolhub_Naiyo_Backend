from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models.user import User
from models.loan_case import LoanCase
from models.loan_calculation import LoanCalculation
from schemas.calculation import LoanCalculationCreate, LoanCalculationResponse
from routes.auth import get_current_user
import math

router = APIRouter()

@router.post("", response_model=LoanCalculationResponse)
def calculate_loan(calc_data: LoanCalculationCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    loan_case = db.query(LoanCase).filter(LoanCase.id == calc_data.case_id, LoanCase.banker_id == current_user.id).first()
    if not loan_case:
        raise HTTPException(status_code=404, detail="Case not found")

    principal = calc_data.principal
    rate_per_month = (calc_data.interest_rate / 12) / 100
    tenure = calc_data.tenure_months

    # EMI calculation
    if rate_per_month > 0:
        emi = (principal * rate_per_month * math.pow(1 + rate_per_month, tenure)) / (math.pow(1 + rate_per_month, tenure) - 1)
    else:
        emi = principal / tenure

    total_payment = emi * tenure
    total_interest = total_payment - principal

    calc = LoanCalculation(
        case_id=calc_data.case_id,
        principal=principal,
        interest_rate=calc_data.interest_rate,
        tenure_months=tenure,
        emi=round(emi, 2),
        total_interest=round(total_interest, 2),
        total_payment=round(total_payment, 2)
    )
    
    db.add(calc)
    db.commit()
    db.refresh(calc)
    return calc

@router.get("/case/{case_id}", response_model=list[LoanCalculationResponse])
def get_case_calculations(case_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    loan_case = db.query(LoanCase).filter(LoanCase.id == case_id, LoanCase.banker_id == current_user.id).first()
    if not loan_case:
        raise HTTPException(status_code=404, detail="Case not found")
        
    calcs = db.query(LoanCalculation).filter(LoanCalculation.case_id == case_id).all()
    return calcs
