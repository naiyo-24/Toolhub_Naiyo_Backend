from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models.user import User
from models.case_event import CaseEvent
from models.loan_case import LoanCase
from schemas.task import CaseEventResponse
from routes.auth import get_current_user

router = APIRouter()

@router.get("/case/{case_id}", response_model=list[CaseEventResponse])
def get_case_timeline(case_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    loan_case = db.query(LoanCase).filter(LoanCase.id == case_id, LoanCase.banker_id == current_user.id).first()
    if not loan_case:
        raise HTTPException(status_code=404, detail="Case not found")
        
    events = db.query(CaseEvent).filter(CaseEvent.case_id == case_id).order_by(CaseEvent.created_at.desc()).all()
    return events
