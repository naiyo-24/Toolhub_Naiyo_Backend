from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_
from database import get_db
from models.user import User
from models.customer import Customer
from models.loan_case import LoanCase
from schemas.customer import CustomerResponse
from schemas.case import LoanCaseResponse
from routes.auth import get_current_user
from pydantic import BaseModel

router = APIRouter()

class SearchResponse(BaseModel):
    customers: list[CustomerResponse]
    cases: list[LoanCaseResponse]

@router.get("/loandesk", response_model=SearchResponse)
def search_loandesk(
    q: str = Query(..., min_length=1, description="Search query for name, PAN, or Case ID"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    search_term = f"%{q}%"
    
    # Search Customers by full_name or pan
    customers = db.query(Customer).filter(
        Customer.created_by == current_user.id,
        or_(
            Customer.full_name.ilike(search_term),
            Customer.pan.ilike(search_term)
        )
    ).all()
    
    # Search Cases by case_number
    cases = db.query(LoanCase).filter(
        LoanCase.banker_id == current_user.id,
        LoanCase.case_number.ilike(search_term)
    ).all()
    
    return SearchResponse(
        customers=customers,
        cases=cases
    )
