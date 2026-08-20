from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from database import get_db
from models.user import User
from models.loan_case import LoanCase
from schemas.case import LoanCaseCreate, LoanCaseUpdate, LoanCaseResponse
from routes.auth import get_current_user

router = APIRouter()

@router.get("", response_model=list[LoanCaseResponse])
def get_cases(
    status: str = Query(None, description="Filter by status"),
    current_user: User = Depends(get_current_user), 
    db: Session = Depends(get_db)
):
    query = db.query(LoanCase).filter(LoanCase.banker_id == current_user.id)
    if status:
        query = query.filter(LoanCase.status == status)
    return query.all()

@router.post("", response_model=LoanCaseResponse)
def create_case(case_data: LoanCaseCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    loan_case = LoanCase(
        customer_id=case_data.customer_id,
        banker_id=current_user.id,
        organization_id=case_data.organization_id,
        loan_type=case_data.loan_type,
        loan_purpose=case_data.loan_purpose,
        requested_amount=case_data.requested_amount,
        tenure_months=case_data.tenure_months,
        interest_rate=case_data.interest_rate,
        monthly_income=case_data.monthly_income,
        other_income=case_data.other_income,
        existing_emi=case_data.existing_emi,
        existing_liabilities=case_data.existing_liabilities,
        status=case_data.status or "DRAFT"
    )
    db.add(loan_case)
    db.commit()
    db.refresh(loan_case)
    return loan_case

@router.get("/{case_id}", response_model=LoanCaseResponse)
def get_case(case_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    loan_case = db.query(LoanCase).filter(LoanCase.id == case_id, LoanCase.banker_id == current_user.id).first()
    if not loan_case:
        raise HTTPException(status_code=404, detail="Case not found")
    return loan_case

@router.patch("/{case_id}", response_model=LoanCaseResponse)
def update_case(case_id: int, case_data: LoanCaseUpdate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    loan_case = db.query(LoanCase).filter(LoanCase.id == case_id, LoanCase.banker_id == current_user.id).first()
    if not loan_case:
        raise HTTPException(status_code=404, detail="Case not found")

    update_data = case_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(loan_case, key, value)

    db.commit()
    db.refresh(loan_case)
    return loan_case

@router.get("/{case_id}/download-report")
def download_case_report(case_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    from fastapi.responses import FileResponse
    from utils.pdf_generator import generate_case_report
    import os
    
    # Ensure case belongs to user
    loan_case = db.query(LoanCase).filter(LoanCase.id == case_id, LoanCase.banker_id == current_user.id).first()
    if not loan_case:
        raise HTTPException(status_code=404, detail="Case not found")
        
    try:
        pdf_path = generate_case_report(case_id, db)
        if not os.path.exists(pdf_path):
            raise HTTPException(status_code=500, detail="Failed to generate report")
            
        return FileResponse(
            path=pdf_path, 
            filename=os.path.basename(pdf_path),
            media_type="application/pdf",
            headers={"Content-Disposition": f"inline; filename={os.path.basename(pdf_path)}"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
