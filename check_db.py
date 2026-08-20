from database import SessionLocal
from models.loan_case import LoanCase
from models.customer import Customer
from models.user import User
from models.organization import Organization

db = SessionLocal()
case = db.query(LoanCase).order_by(LoanCase.id.desc()).first()
print(f"ID: {case.id}")
print(f"Case Number: {case.case_number}")
print(f"Requested Amount: {case.requested_amount}")
