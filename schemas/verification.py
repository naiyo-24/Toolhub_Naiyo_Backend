from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class VerificationBase(BaseModel):
    verification_type: str
    status: Optional[str] = "NOT_CHECKED"
    source: Optional[str] = None
    reference_number: Optional[str] = None
    verified_name: Optional[str] = None
    verified_address: Optional[str] = None
    remarks: Optional[str] = None

class VerificationCreate(VerificationBase):
    case_id: int
    document_id: Optional[int] = None

class VerificationUpdate(BaseModel):
    status: Optional[str] = None
    source: Optional[str] = None
    reference_number: Optional[str] = None
    verified_name: Optional[str] = None
    verified_address: Optional[str] = None
    remarks: Optional[str] = None

class VerificationResponse(VerificationBase):
    id: int
    case_id: int
    document_id: Optional[int] = None
    verified_by: Optional[int] = None
    verified_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True

class CaseDocumentRequirementBase(BaseModel):
    document_type: str
    is_required: Optional[bool] = True
    status: Optional[str] = "MISSING"

class CaseDocumentRequirementCreate(CaseDocumentRequirementBase):
    case_id: int

class CaseDocumentRequirementUpdate(BaseModel):
    is_required: Optional[bool] = None
    status: Optional[str] = None

class CaseDocumentRequirementResponse(CaseDocumentRequirementBase):
    id: int
    case_id: int
    received_at: Optional[datetime] = None
    verified_at: Optional[datetime] = None

    class Config:
        from_attributes = True
