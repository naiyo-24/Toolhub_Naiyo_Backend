from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models.user import User
from models.loan_case import LoanCase
from models.verification import Verification, CaseDocumentRequirement
from schemas.verification import VerificationCreate, VerificationUpdate, VerificationResponse, CaseDocumentRequirementCreate, CaseDocumentRequirementUpdate, CaseDocumentRequirementResponse
from routes.auth import get_current_user
from datetime import datetime

router = APIRouter()

@router.get("/case/{case_id}", response_model=list[VerificationResponse])
def get_case_verifications(case_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    loan_case = db.query(LoanCase).filter(LoanCase.id == case_id, LoanCase.banker_id == current_user.id).first()
    if not loan_case:
        raise HTTPException(status_code=404, detail="Case not found")
        
    verifications = db.query(Verification).filter(Verification.case_id == case_id).all()
    return verifications

@router.post("", response_model=VerificationResponse)
def create_verification(verif_data: VerificationCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    loan_case = db.query(LoanCase).filter(LoanCase.id == verif_data.case_id, LoanCase.banker_id == current_user.id).first()
    if not loan_case:
        raise HTTPException(status_code=404, detail="Case not found")

    verification = Verification(
        case_id=verif_data.case_id,
        document_id=verif_data.document_id,
        verification_type=verif_data.verification_type,
        status=verif_data.status or "NOT_CHECKED",
        source=verif_data.source,
        reference_number=verif_data.reference_number,
        verified_name=verif_data.verified_name,
        verified_address=verif_data.verified_address,
        remarks=verif_data.remarks
    )
    if verification.status in ["VERIFIED", "FAILED"]:
        verification.verified_by = current_user.id
        verification.verified_at = datetime.utcnow()

    db.add(verification)
    db.commit()
    db.refresh(verification)
    return verification

@router.patch("/{verif_id}", response_model=VerificationResponse)
def update_verification(verif_id: int, verif_data: VerificationUpdate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    verification = db.query(Verification).filter(Verification.id == verif_id).first()
    if not verification:
        raise HTTPException(status_code=404, detail="Verification not found")

    update_data = verif_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(verification, key, value)
        
    if "status" in update_data and update_data["status"] in ["VERIFIED", "FAILED"]:
        verification.verified_by = current_user.id
        verification.verified_at = datetime.utcnow()

    db.commit()
    db.refresh(verification)
    return verification
