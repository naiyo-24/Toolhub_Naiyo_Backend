from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
import datetime

class FormFieldCreate(BaseModel):
    label: str = Field(..., description="The question text")
    field_type: str = Field(..., description="text, email, dropdown, radio, checkbox, etc.")
    is_required: bool = Field(False)
    options: Optional[List[str]] = Field(None, description="Options for dropdown/radio/checkbox")
    order_index: int = Field(0)

class FormCreate(BaseModel):
    title: str = Field(..., description="Form Title")
    description: Optional[str] = Field(None)
    header_image_url: Optional[str] = Field(None, description="URL of the header image")
    form_type: str = Field("Survey", description="Template type (e.g., Contact Form, Quiz Builder)")
    is_published: bool = Field(True)
    allow_multiple_responses: bool = Field(True)
    fields: List[FormFieldCreate] = Field(..., description="List of fields to create with the form")

class FormDetailModel(BaseModel):
    id: str
    title: str
    description: Optional[str] = None
    header_image_url: Optional[str] = None
    form_type: str = "Survey"
    is_published: bool = True
    allow_multiple_responses: bool = True
    fields: List[FormFieldCreate]

class FormResponseSubmit(BaseModel):
    respondent_email: Optional[str] = Field(None)
    answers: Dict[str, Any] = Field(..., description="JSON object mapping Field IDs (as strings) to answer values")
