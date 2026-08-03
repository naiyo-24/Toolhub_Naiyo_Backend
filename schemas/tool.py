from pydantic import BaseModel
from typing import Optional

class ToolBase(BaseModel):
    name: str
    description: Optional[str] = None
    url: Optional[str] = None

class ToolCreate(ToolBase):
    pass

class ToolResponse(ToolBase):
    id: int

    class Config:
        from_attributes = True
