from pydantic import BaseModel
from typing import Optional
from datetime import date, datetime

class TaskBase(BaseModel):
    title: str
    description: Optional[str] = None
    assigned_to: Optional[int] = None
    status: Optional[str] = "TODO"
    priority: Optional[str] = "MEDIUM"
    due_date: Optional[date] = None

class TaskCreate(TaskBase):
    case_id: int

class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    assigned_to: Optional[int] = None
    status: Optional[str] = None
    priority: Optional[str] = None
    due_date: Optional[date] = None

class TaskResponse(TaskBase):
    id: int
    case_id: int
    created_by: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class CaseEventBase(BaseModel):
    event_type: str
    description: str

class CaseEventCreate(CaseEventBase):
    case_id: int

class CaseEventResponse(CaseEventBase):
    id: int
    case_id: int
    actor_id: Optional[int] = None
    created_at: datetime

    class Config:
        from_attributes = True

class NotificationResponse(BaseModel):
    id: int
    title: str
    message: str
    notification_type: Optional[str] = None
    related_entity_id: Optional[int] = None
    is_read: bool
    created_at: datetime

    class Config:
        from_attributes = True
