from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models.user import User
from models.task import Task
from models.loan_case import LoanCase
from schemas.task import TaskCreate, TaskUpdate, TaskResponse
from routes.auth import get_current_user

router = APIRouter()

@router.get("/case/{case_id}", response_model=list[TaskResponse])
def get_case_tasks(case_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    loan_case = db.query(LoanCase).filter(LoanCase.id == case_id, LoanCase.banker_id == current_user.id).first()
    if not loan_case:
        raise HTTPException(status_code=404, detail="Case not found")
        
    tasks = db.query(Task).filter(Task.case_id == case_id).all()
    return tasks

@router.post("", response_model=TaskResponse)
def create_task(task_data: TaskCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    loan_case = db.query(LoanCase).filter(LoanCase.id == task_data.case_id, LoanCase.banker_id == current_user.id).first()
    if not loan_case:
        raise HTTPException(status_code=404, detail="Case not found")

    task = Task(
        case_id=task_data.case_id,
        assigned_to=task_data.assigned_to,
        title=task_data.title,
        description=task_data.description,
        status=task_data.status or "TODO",
        priority=task_data.priority or "MEDIUM",
        due_date=task_data.due_date,
        created_by=current_user.id
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    return task

@router.patch("/{task_id}", response_model=TaskResponse)
def update_task(task_id: int, task_data: TaskUpdate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    update_data = task_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(task, key, value)

    db.commit()
    db.refresh(task)
    return task
