from pydantic import BaseModel
from typing import Optional

class DocumentBase(BaseModel):
    document_type: str
    file_name: str
    mime_type: Optional[str] = None
    file_size: Optional[int] = None
    page_count: Optional[int] = None
    storage_type: Optional[str] = "LOCAL"

class DocumentCreate(DocumentBase):
    case_id: int

class DocumentResponse(DocumentBase):
    id: int
    case_id: int
    storage_key: str
    file_hash: Optional[str] = None
    ocr_status: Optional[str] = None
    verification_status: Optional[str] = None
    document_status: Optional[str] = None
    created_by: int

    class Config:
        from_attributes = True

class DocumentAccessResponse(BaseModel):
    document_id: int
    file_name: str
    url: str
