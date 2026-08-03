from pydantic import BaseModel, Field
from typing import List, Optional

# --- AI Tools ---
class ResumeBuilderRequest(BaseModel):
    full_name: str
    email: str
    phone: Optional[str] = None
    education: str = Field(..., description="Details about education")
    experience: str = Field(..., description="Work experience details")
    skills: List[str] = Field(..., description="List of technical and soft skills")
    target_role: str = Field(..., description="The job role you are applying for")

class IDCardRequest(BaseModel):
    name: str
    role: str
    organization: str
    id_number: str
    blood_group: Optional[str] = None
    card_type: str = Field("Corporate", description="e.g., School, College, Office, Event")
