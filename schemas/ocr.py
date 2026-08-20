from pydantic import BaseModel
from typing import Optional, Dict, Any

class OCRResultBase(BaseModel):
    raw_text: Optional[str] = None
    structured_data: Optional[Dict[str, Any]] = None
    confidence: Optional[float] = None
    language: Optional[str] = None

class OCRResultCreate(OCRResultBase):
    document_id: int

class OCRResultUpdate(OCRResultBase):
    pass

class OCRResultResponse(OCRResultBase):
    id: int
    document_id: int

    class Config:
        from_attributes = True
