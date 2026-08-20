from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_
from database import get_db
from models.user import User
from models.customer import Customer
from schemas.customer import CustomerCreate, CustomerUpdate, CustomerResponse
from routes.auth import get_current_user

router = APIRouter()

@router.get("", response_model=list[CustomerResponse])
def get_customers(
    q: str = Query(None, description="Search query"),
    current_user: User = Depends(get_current_user), 
    db: Session = Depends(get_db)
):
    query = db.query(Customer)
    if q:
        search_term = f"%{q}%"
        query = query.filter(
            or_(
                Customer.full_name.ilike(search_term),
                Customer.mobile.ilike(search_term),
                Customer.pan.ilike(search_term),
                Customer.gstin.ilike(search_term),
                Customer.udyam_number.ilike(search_term),
                Customer.business_name.ilike(search_term)
            )
        )
    return query.all()

@router.post("", response_model=CustomerResponse)
def create_customer(customer_data: CustomerCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    # Check if PAN already exists, for example
    if customer_data.pan:
        existing = db.query(Customer).filter(Customer.pan == customer_data.pan).first()
        if existing:
            raise HTTPException(status_code=400, detail="Customer with this PAN already exists")

    customer = Customer(
        customer_type=customer_data.customer_type,
        full_name=customer_data.full_name,
        mobile=customer_data.mobile,
        email=customer_data.email,
        pan=customer_data.pan,
        dob=customer_data.dob,
        occupation=customer_data.occupation,
        address=customer_data.address,
        legal_name=customer_data.legal_name,
        business_name=customer_data.business_name,
        business_type=customer_data.business_type,
        gstin=customer_data.gstin,
        udyam_number=customer_data.udyam_number,
        created_by=current_user.id
    )
    db.add(customer)
    db.commit()
    db.refresh(customer)
    return customer

@router.get("/{customer_id}", response_model=CustomerResponse)
def get_customer(customer_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    return customer

@router.patch("/{customer_id}", response_model=CustomerResponse)
def update_customer(customer_id: int, customer_data: CustomerUpdate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")

    update_data = customer_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(customer, key, value)

    db.commit()
    db.refresh(customer)
    return customer
