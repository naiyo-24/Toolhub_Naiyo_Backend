from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSONB
from database import Base
import datetime
import uuid

def generate_uuid():
    return str(uuid.uuid4())

class Form(Base):
    __tablename__ = "forms"
    
    # We use a UUID string as the primary key so the public share link is secure and unguessable!
    id = Column(String, primary_key=True, default=generate_uuid, index=True)
    user_id = Column(Integer, index=True, default=1)
    title = Column(String)
    description = Column(Text, nullable=True)
    header_image_url = Column(String, nullable=True)
    form_type = Column(String) # e.g. "Survey", "Quiz", "Contact Form"
    is_published = Column(Boolean, default=True)
    allow_multiple_responses = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    fields = relationship("FormField", back_populates="form", cascade="all, delete-orphan")
    responses = relationship("FormResponse", back_populates="form", cascade="all, delete-orphan")

class FormField(Base):
    __tablename__ = "form_fields"
    
    id = Column(Integer, primary_key=True, index=True)
    form_id = Column(String, ForeignKey("forms.id"))
    label = Column(String) # The actual question
    field_type = Column(String) # "text", "email", "dropdown", "radio", "checkbox"
    is_required = Column(Boolean, default=False)
    options = Column(JSONB, nullable=True) # Array of choices if dropdown/radio/checkbox
    order_index = Column(Integer, default=0)
    
    form = relationship("Form", back_populates="fields")

class FormResponse(Base):
    __tablename__ = "form_responses"
    
    id = Column(Integer, primary_key=True, index=True)
    form_id = Column(String, ForeignKey("forms.id"))
    respondent_email = Column(String, nullable=True) # Optional tracking
    respondent_device = Column(String, nullable=True)
    respondent_ip = Column(String, nullable=True)
    submitted_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    # Store answers as a JSON object mapping Field IDs to Answer values
    # e.g., {"12": "Sayar", "13": "Blue", "14": ["Option A", "Option C"]}
    answers = Column(JSONB) 
    
    form = relationship("Form", back_populates="responses")
