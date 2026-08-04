from pydantic import BaseModel, EmailStr
from datetime import datetime

class ContactMessageCreate(BaseModel):
    name: str
    email: EmailStr
    message: str

class ContactMessageResponse(BaseModel):
    id: int
    name: str
    email: EmailStr
    message: str
    created_at: datetime

    class Config:
        orm_mode = True
        from_attributes = True
