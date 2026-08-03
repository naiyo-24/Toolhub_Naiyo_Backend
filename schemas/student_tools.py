from pydantic import BaseModel, Field
from typing import List, Optional

# --- Calculators (Math) ---
class CourseGrade(BaseModel):
    credits: float = Field(..., gt=0)
    grade_points: float = Field(..., ge=0, le=10)

class SemesterResult(BaseModel):
    sgpa: float = Field(..., ge=0, le=10)
    credits: float = Field(..., gt=0)

class CGPARequest(BaseModel):
    semesters: List[SemesterResult] = Field(..., min_items=1)

class SGPARequest(BaseModel):
    courses: List[CourseGrade] = Field(..., min_items=1)

class AttendanceCalcRequest(BaseModel):
    classes_attended: int = Field(..., ge=0)
    total_classes: int = Field(..., gt=0)
    target_percentage: float = Field(..., gt=0, le=100)

class ScientificCalcRequest(BaseModel):
    expression: str = Field(..., min_length=1, max_length=200)

class ExamCountdownRequest(BaseModel):
    exam_date: str = Field(..., description="Format: YYYY-MM-DD")
    exam_name: Optional[str] = None

# --- AI Generators (Text Input) ---
class MockTestRequest(BaseModel):
    topic: str
    difficulty: str = Field("Medium")
    num_questions: int = Field(5, ge=1, le=20)

class QuizGeneratorRequest(BaseModel):
    topic: str
    difficulty: str = Field("Medium")
    num_questions: int = Field(5, ge=1, le=20)

from enum import Enum

class CitationFormat(str, Enum):
    APA = "APA"
    MLA = "MLA"
    CHICAGO = "Chicago"
    HARVARD = "Harvard"
    IEEE = "IEEE"
    AMA = "AMA"
    VANCOUVER = "Vancouver"
    TURABIAN = "Turabian"
    ACS = "ACS"
    AIP = "AIP"
    ASCE = "ASCE"
    BLUEBOOK = "Bluebook"
    OSCOLA = "OSCOLA"
    OTHER = "Other"

class CitationGeneratorRequest(BaseModel):
    source: str = Field(..., description="URL, book title, or article name")
    format: CitationFormat = Field(CitationFormat.APA, description="Select the citation format")
    custom_format: Optional[str] = Field(None, description="Specify if format is 'Other'")

class StudyPlannerRequest(BaseModel):
    subjects: List[str]
    days_available: int = Field(..., gt=0)
    hours_per_day: float = Field(..., gt=0)

class FlashcardsRequest(BaseModel):
    topic: str
    num_cards: int = Field(5, ge=1, le=20)

class NotesMakerRequest(BaseModel):
    topic: str
    detail_level: str = Field("Detailed", description="Brief, Detailed, or Comprehensive")

class TimetableRequest(BaseModel):
    subjects: List[str]
    start_time: str = Field("09:00 AM")
    end_time: str = Field("05:00 PM")

class AssignmentPlannerRequest(BaseModel):
    assignment_topic: str
    days_until_due: int = Field(..., gt=0)

class FormulaBookRequest(BaseModel):
    topic: str = Field(..., description="e.g., 'Kinematics', 'Trigonometry', 'Calculus derivatives'")

# Note: AINoteSummarizer and ResearchSummarizer will use Form data + UploadFile in the router instead of Pydantic models.
