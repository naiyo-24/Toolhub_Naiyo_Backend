from pydantic import BaseModel
from typing import Optional

class MeetingSummarizerRequest(BaseModel):
    transcript: str

class NotesGeneratorRequest(BaseModel):
    topic: str
    context: Optional[str] = None

class AITranslatorRequest(BaseModel):
    text: str
    target_language: str

class EmailWriterRequest(BaseModel):
    context: str
    tone: Optional[str] = "Professional"
    recipient: Optional[str] = None

class GrammarCheckerRequest(BaseModel):
    text: str

class ResumeReviewerRequest(BaseModel):
    resume_text: str

class InterviewPrepRequest(BaseModel):
    job_role: str
    experience_level: Optional[str] = "Entry level"

class HomeworkHelperRequest(BaseModel):
    question: str
    subject: Optional[str] = None

class CodeExplainerRequest(BaseModel):
    code: str
    language: Optional[str] = None

class PromptGeneratorRequest(BaseModel):
    idea: str
