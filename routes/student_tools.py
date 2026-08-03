from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from schemas.student_tools import *
from routes.ai_tools import generate_ai_response, upload_to_gemini
import mimetypes
from datetime import datetime

router = APIRouter(prefix="/student-toolkit", tags=["Student Toolkit"])

# ---------------------------------------------------------
# CALCULATORS (Math & Logic)
# ---------------------------------------------------------

@router.post("/cgpa-calculator")
def calculate_cgpa(req: CGPARequest):
    total_credits = sum(sem.credits for sem in req.semesters)
    if total_credits == 0:
        raise HTTPException(status_code=400, detail="Total credits cannot be zero.")
        
    total_points = sum(sem.credits * sem.sgpa for sem in req.semesters)
    cgpa = total_points / total_credits
    return {"cgpa": round(cgpa, 2)}

@router.post("/sgpa-calculator")
def calculate_sgpa(req: SGPARequest):
    total_credits = sum(course.credits for course in req.courses)
    if total_credits == 0:
        raise HTTPException(status_code=400, detail="Total credits cannot be zero.")
        
    total_points = sum(course.credits * course.grade_points for course in req.courses)
    sgpa = total_points / total_credits
    return {"sgpa": round(sgpa, 2)}

@router.post("/attendance-calculator")
def calculate_attendance(req: AttendanceCalcRequest):
    if req.classes_attended > req.total_classes:
        raise HTTPException(status_code=400, detail="Classes attended cannot be greater than total classes.")
        
    current_percentage = (req.classes_attended / req.total_classes) * 100 if req.total_classes > 0 else 0
    target = req.target_percentage
    
    if current_percentage >= target:
        # How many can they bunk?
        # (attended) / (total + bunk) = target / 100
        # bunk = (attended * 100 / target) - total
        can_bunk = int((req.classes_attended * 100 / target) - req.total_classes)
        return {
            "current_percentage": round(current_percentage, 2),
            "status": "Safe",
            "message": f"You can safely bunk {can_bunk} classes and stay at or above {target}%."
        }
    else:
        # How many do they need to attend?
        # (attended + required) / (total + required) = target / 100
        # attended + req = (total * target / 100) + (req * target / 100)
        # req * (1 - target/100) = (total * target / 100) - attended
        req_classes = ((req.total_classes * target / 100) - req.classes_attended) / (1 - target / 100)
        import math
        req_classes = math.ceil(req_classes)
        return {
            "current_percentage": round(current_percentage, 2),
            "status": "Shortage",
            "message": f"You need to attend {req_classes} more consecutive classes to reach {target}%."
        }

@router.post("/scientific-calculator")
def scientific_calculator(req: ScientificCalcRequest):
    import ast
    import math
    import operator

    # Very basic and safe math evaluator
    allowed_operators = {
        ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul,
        ast.Div: operator.truediv, ast.Pow: operator.pow, ast.BitXor: operator.xor,
        ast.USub: operator.neg
    }
    allowed_funcs = {
        'sin': math.sin, 'cos': math.cos, 'tan': math.tan,
        'sqrt': math.sqrt, 'log': math.log, 'log10': math.log10,
        'pi': math.pi, 'e': math.e
    }

    def evaluate(node):
        if isinstance(node, ast.Num):
            return node.n
        elif isinstance(node, ast.BinOp):
            return allowed_operators[type(node.op)](evaluate(node.left), evaluate(node.right))
        elif isinstance(node, ast.UnaryOp):
            return allowed_operators[type(node.op)](evaluate(node.operand))
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name) and node.func.id in allowed_funcs:
                return allowed_funcs[node.func.id](evaluate(node.args[0]))
        elif isinstance(node, ast.Name):
            if node.id in allowed_funcs:
                return allowed_funcs[node.id]
        raise ValueError("Invalid mathematical expression")

    try:
        expr = req.expression.replace("^", "**")
        node = ast.parse(expr, mode='eval').body
        result = evaluate(node)
        return {"result": round(result, 4) if isinstance(result, float) else result}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid expression: {str(e)}")

@router.post("/exam-countdown")
def exam_countdown(req: ExamCountdownRequest):
    try:
        exam_date = datetime.strptime(req.exam_date, "%Y-%m-%d")
        now = datetime.now()
        diff = exam_date - now
        
        if diff.total_seconds() < 0:
            return {"status": "Passed", "message": "This exam has already passed."}
            
        days = diff.days
        hours = diff.seconds // 3600
        return {
            "status": "Upcoming",
            "days_left": days,
            "hours_left": hours,
            "message": f"You have {days} days and {hours} hours left until the exam."
        }
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")

# ---------------------------------------------------------
# AI GENERATORS
# ---------------------------------------------------------

@router.post("/ai-note-summarizer")
async def ai_note_summarizer(file: UploadFile = File(None), notes_text: str = Form(None)):
    if not file and not notes_text:
        raise HTTPException(status_code=400, detail="Provide either a file or text notes")
        
    prompt = "Act as an expert academic summarizer. Summarize the following notes into clear, bulleted study points."
    file_uri = None
    if file:
        file_bytes = await file.read()
        mime = mimetypes.guess_type(file.filename)[0] or "application/pdf"
        file_uri = upload_to_gemini(file_bytes, file.filename, mime)
        if notes_text: prompt += f"\n\nAdditional text:\n{notes_text}"
    else:
        prompt += f"\n\nNotes:\n{notes_text}"
        
    return {"summary": generate_ai_response(prompt, file_uri=file_uri)}

import json

def clean_json_string(raw: str) -> str:
    raw = raw.strip()
    if raw.startswith("```json"):
        raw = raw[7:]
    elif raw.startswith("```"):
        raw = raw[3:]
    if raw.endswith("```"):
        raw = raw[:-3]
    return raw.strip()

@router.post("/mock-tests")
def mock_tests(req: MockTestRequest):
    prompt = f"Generate a {req.difficulty} mock test about '{req.topic}' with {req.num_questions} multiple-choice questions. Return a JSON array of objects with keys: 'question', 'options' (array of strings), and 'correct_answer'."
    raw_json = clean_json_string(generate_ai_response(prompt, json_mode=True))
    try:
        return {"mock_test": json.loads(raw_json)}
    except json.JSONDecodeError:
        return {"mock_test": raw_json}

@router.post("/quiz-generator")
def quiz_generator(req: QuizGeneratorRequest):
    prompt = f"Generate a {req.difficulty} quiz about '{req.topic}' with {req.num_questions} short-answer questions. Return a JSON array of objects with keys: 'question' and 'answer'."
    raw_json = clean_json_string(generate_ai_response(prompt, json_mode=True))
    try:
        return {"quiz": json.loads(raw_json)}
    except json.JSONDecodeError:
        return {"quiz": raw_json}

@router.post("/timetable")
def generate_timetable(req: TimetableRequest):
    subs = ", ".join(req.subjects)
    prompt = f"Create a structured daily study timetable from {req.start_time} to {req.end_time}, dividing the time effectively between these subjects: {subs}. Include short breaks."
    return {"timetable": generate_ai_response(prompt)}

@router.post("/assignment-planner")
def assignment_planner(req: AssignmentPlannerRequest):
    prompt = f"I have {req.days_until_due} days left to complete an assignment on '{req.assignment_topic}'. Generate a day-by-day checklist plan to get it done efficiently."
    return {"planner": generate_ai_response(prompt)}

@router.post("/study-planner")
def study_planner(req: StudyPlannerRequest):
    subs = ", ".join(req.subjects)
    prompt = f"I have {req.days_available} days left to study {subs}. I can study {req.hours_per_day} hours per day. Generate a comprehensive day-by-day study schedule."
    return {"study_plan": generate_ai_response(prompt)}

@router.post("/flashcards")
def generate_flashcards(req: FlashcardsRequest):
    prompt = f"Generate {req.num_cards} highly effective study flashcards for the topic '{req.topic}'. Return a JSON array of objects with keys: 'question' and 'answer'."
    raw_json = clean_json_string(generate_ai_response(prompt, json_mode=True))
    try:
        return {"flashcards": json.loads(raw_json)}
    except json.JSONDecodeError:
        return {"flashcards": raw_json}

@router.post("/notes-maker")
def notes_maker(req: NotesMakerRequest):
    prompt = f"Generate {req.detail_level.lower()} digital study notes on the topic '{req.topic}'. Structure it beautifully with headings and bullet points."
    return {"notes": generate_ai_response(prompt)}

@router.post("/citation-generator")
def citation_generator(req: CitationGeneratorRequest):
    fmt = req.custom_format if req.format == "Other" and req.custom_format else req.format.value
    prompt = f"Generate a proper academic citation in {fmt} format for the following source: '{req.source}'. Only return the citation text."
    return {"citation": generate_ai_response(prompt)}

@router.post("/formula-book")
def formula_book(req: FormulaBookRequest):
    prompt = f"List all the essential mathematical/scientific formulas related to '{req.topic}'. Return a JSON array of objects with keys: 'formula_name', 'equation', and 'description'."
    raw_json = clean_json_string(generate_ai_response(prompt, json_mode=True))
    try:
        return {"formulas": json.loads(raw_json)}
    except json.JSONDecodeError:
        return {"formulas": raw_json}

@router.post("/research-summarizer")
async def research_summarizer(file: UploadFile = File(None), paper_text: str = Form(None)):
    if not file and not paper_text:
        raise HTTPException(status_code=400, detail="Provide either a research paper file or text")
        
    prompt = "Act as an expert researcher. Read the provided research paper and summarize the abstract, methodology, key findings, and conclusion in plain English."
    file_uri = None
    if file:
        file_bytes = await file.read()
        mime = mimetypes.guess_type(file.filename)[0] or "application/pdf"
        file_uri = upload_to_gemini(file_bytes, file.filename, mime)
        if paper_text: prompt += f"\n\nAdditional context:\n{paper_text}"
    else:
        prompt += f"\n\nPaper Text:\n{paper_text}"
        
    return {"summary": generate_ai_response(prompt, file_uri=file_uri)}
