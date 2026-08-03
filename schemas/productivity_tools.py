from pydantic import BaseModel, Field
from typing import Optional
import datetime

class TodoRequest(BaseModel):
    title: str = Field(..., description="Task title")
    description: Optional[str] = Field(None, description="Task details")
    due_date: Optional[datetime.datetime] = Field(None, description="Due date and time")
    priority: str = Field("Medium", description="Low, Medium, High")

class NoteRequest(BaseModel):
    title: str = Field(..., description="Note title")
    content: str = Field(..., description="Note content")

class FocusSessionRequest(BaseModel):
    session_type: str = Field("Pomodoro", description="Pomodoro or Custom")
    duration_minutes: int = Field(25, description="Duration in minutes")

class ClipboardRequest(BaseModel):
    content: str = Field(..., description="Text to copy to clipboard")

class JournalRequest(BaseModel):
    content: str = Field(..., description="Journal entry")
    mood: Optional[str] = Field(None, description="Mood (e.g. Happy, Sad)")

class GoalRequest(BaseModel):
    title: str = Field(..., description="Goal title")
    target_date: Optional[datetime.date] = Field(None, description="Target completion date")

class GoalProgressRequest(BaseModel):
    progress_percentage: float = Field(..., description="Progress from 0 to 100")

class ReminderRequest(BaseModel):
    title: str = Field(..., description="Alert title")
    trigger_time: datetime.datetime = Field(..., description="When to trigger the alert")

class CalendarEventRequest(BaseModel):
    title: str = Field(..., description="Event title")
    description: Optional[str] = Field(None, description="Event details")
    start_time: datetime.datetime = Field(..., description="Start time")
    end_time: datetime.datetime = Field(..., description="End time")
