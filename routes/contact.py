from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db
from models.contact import ContactMessage
from schemas.contact import ContactMessageCreate, ContactMessageResponse

router = APIRouter(
    tags=["Contact"]
)

@router.post("/", response_model=ContactMessageResponse)
def submit_contact_form(contact: ContactMessageCreate, db: Session = Depends(get_db)):
    db_contact = ContactMessage(
        name=contact.name,
        email=contact.email,
        message=contact.message
    )
    db.add(db_contact)
    db.commit()
    db.refresh(db_contact)
    return db_contact
