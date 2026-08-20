from database import SessionLocal
from models.loan_case import LoanCase
from models.customer import Customer
from models.user import User
from models.organization import Organization

db = SessionLocal()
case = db.query(LoanCase).filter_by(id=1).first()
case.requested_amount = 2000000.0
db.commit()
print("Updated successfully")
