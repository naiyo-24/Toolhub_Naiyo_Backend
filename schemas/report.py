from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class ReportBase(BaseModel):
    report_type: str
    status: Optional[str] = "GENERATED"

class ReportCreate(ReportBase):
    case_id: int

class ReportResponse(ReportBase):
    id: int
    case_id: int
    file_path: Optional[str] = None
    generated_by: int
    created_at: datetime

    class Config:
        from_attributes = True
