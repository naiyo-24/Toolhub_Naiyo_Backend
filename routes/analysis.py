from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models.user import User
from models.loan_case import LoanCase
from models.bank_statement import BankStatement
from models.financial_analysis import FinancialAnalysis
from schemas.analysis import BankStatementCreate, BankStatementUpdate, BankStatementResponse, FinancialAnalysisCreate, FinancialAnalysisUpdate, FinancialAnalysisResponse
from routes.auth import get_current_user

router = APIRouter()

@router.post("/statements", response_model=BankStatementResponse)
def create_bank_statement(stmt_data: BankStatementCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    loan_case = db.query(LoanCase).filter(LoanCase.id == stmt_data.case_id, LoanCase.banker_id == current_user.id).first()
    if not loan_case:
        raise HTTPException(status_code=404, detail="Case not found")

    stmt = BankStatement(**stmt_data.model_dump())
    db.add(stmt)
    db.commit()
    db.refresh(stmt)
    return stmt

@router.get("/case/{case_id}/statements", response_model=list[BankStatementResponse])
def get_case_statements(case_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    loan_case = db.query(LoanCase).filter(LoanCase.id == case_id, LoanCase.banker_id == current_user.id).first()
    if not loan_case:
        raise HTTPException(status_code=404, detail="Case not found")
        
    statements = db.query(BankStatement).filter(BankStatement.case_id == case_id).all()
    return statements

@router.post("", response_model=FinancialAnalysisResponse)
def create_financial_analysis(analysis_data: FinancialAnalysisCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    loan_case = db.query(LoanCase).filter(LoanCase.id == analysis_data.case_id, LoanCase.banker_id == current_user.id).first()
    if not loan_case:
        raise HTTPException(status_code=404, detail="Case not found")
        
    existing = db.query(FinancialAnalysis).filter(FinancialAnalysis.case_id == analysis_data.case_id).first()
    if existing:
        raise HTTPException(status_code=400, detail="Analysis already exists for this case. Use PATCH to update.")

    analysis = FinancialAnalysis(**analysis_data.model_dump())
    db.add(analysis)
    db.commit()
    db.refresh(analysis)
    return analysis

@router.get("/case/{case_id}", response_model=FinancialAnalysisResponse)
def get_financial_analysis(case_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    loan_case = db.query(LoanCase).filter(LoanCase.id == case_id, LoanCase.banker_id == current_user.id).first()
    if not loan_case:
        raise HTTPException(status_code=404, detail="Case not found")
        
    analysis = db.query(FinancialAnalysis).filter(FinancialAnalysis.case_id == case_id).first()
    if not analysis:
        raise HTTPException(status_code=404, detail="Financial analysis not found for this case")
    return analysis

@router.patch("/{analysis_id}", response_model=FinancialAnalysisResponse)
def update_financial_analysis(analysis_id: int, analysis_data: FinancialAnalysisUpdate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    analysis = db.query(FinancialAnalysis).filter(FinancialAnalysis.id == analysis_id).first()
    if not analysis:
        raise HTTPException(status_code=404, detail="Financial analysis not found")

    update_data = analysis_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(analysis, key, value)

    db.commit()
    db.refresh(analysis)
    return analysis

from schemas.analysis import RiskAnalysisResponse
from utils.analysis_engine import run_analysis_engine

@router.post("/case/{case_id}/evaluate", response_model=RiskAnalysisResponse)
def evaluate_loan_case(case_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    Runs the LoanDesk Analysis Engine v1.
    Calculates FOIR, Proposed EMI, evaluates Risk Score, and determines Loan Eligibility.
    """
    loan_case = db.query(LoanCase).filter(LoanCase.id == case_id, LoanCase.banker_id == current_user.id).first()
    if not loan_case:
        raise HTTPException(status_code=404, detail="Case not found")

    try:
        risk_analysis = run_analysis_engine(case_id, db)
        return risk_analysis
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

