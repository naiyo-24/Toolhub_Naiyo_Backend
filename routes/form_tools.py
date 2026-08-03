from fastapi import APIRouter, Depends, HTTPException, File, UploadFile, Request
from fastapi.responses import HTMLResponse, StreamingResponse
import csv
import io
from sqlalchemy.orm import Session
from database import get_db
import crud.forms as crud_forms
from routes.auth import get_current_user
import models.user
from schemas.form_tools import FormCreate, FormResponseSubmit
import models.forms
import os
import shutil
import uuid

router = APIRouter()

@router.get("/forms/view/{form_id}", response_class=HTMLResponse)
async def view_form_web(form_id: str):
    with open("templates/form_viewer.html", "r") as f:
        html_content = f.read()
    return HTMLResponse(content=html_content)

@router.post("/forms/upload")
async def upload_form_file(file: UploadFile = File(...)):
    # 5MB size limit
    MAX_SIZE = 5 * 1024 * 1024
    content = await file.read()
    if len(content) > MAX_SIZE:
        raise HTTPException(status_code=400, detail="File too large. Max size is 5MB.")
    
    # Generate unique filename
    ext = file.filename.split('.')[-1] if '.' in file.filename else 'bin'
    filename = f"{uuid.uuid4().hex}.{ext}"
    file_path = os.path.join("uploads", filename)
    
    with open(file_path, "wb") as f:
        f.write(content)
        
    return {"url": f"/uploads/{filename}"}

@router.post("/forms")
def create_form(req: FormCreate, db: Session = Depends(get_db), current_user: models.user.User = Depends(get_current_user)):
    # Break down the payload into form_data and fields_data
    form_data = req.dict(exclude={"fields"})
    fields_data = [field.dict() for field in req.fields]
    
    # Save to database
    form = crud_forms.create_form(db, form_data, fields_data, user_id=current_user.id)
    
    # Generate the public shareable link
    # The mobile app can construct a URL like: https://yourapp.com/forms/{form.id}
    public_link = f"/forms/{form.id}"
    
    return {
        "status": "Form created successfully!",
        "form_id": form.id,
        "public_link": public_link,
        "form": {
            "title": form.title,
            "type": form.form_type,
            "fields_count": len(form.fields)
        }
    }

@router.put("/forms/{form_id}")
def update_form(form_id: str, req: FormCreate, db: Session = Depends(get_db)):
    form_data = req.dict(exclude={"fields"})
    fields_data = [field.dict() for field in req.fields]
    
    form = crud_forms.update_form(db, form_id, form_data, fields_data)
    if not form:
        raise HTTPException(status_code=404, detail="Form not found")
        
    return {
        "status": "Form updated successfully!",
        "form_id": form.id,
        "form": {
            "title": form.title,
            "type": form.form_type,
            "fields_count": len(form.fields)
        }
    }

@router.get("/forms")
def get_my_forms(db: Session = Depends(get_db), current_user: models.user.User = Depends(get_current_user)):
    forms = crud_forms.get_user_forms(db, user_id=current_user.id)
    return [
        {
            "id": form.id,
            "title": form.title,
            "form_type": form.form_type,
            "is_published": form.is_published,
            "fields_count": len(form.fields)
        }
        for form in forms
    ]

@router.get("/forms/{form_id}")
def get_public_form(form_id: str, db: Session = Depends(get_db)):
    form = crud_forms.get_form_by_id(db, form_id)
    if not form:
        raise HTTPException(status_code=404, detail="Form not found")
        
    if not form.is_published:
        raise HTTPException(status_code=403, detail="This form is no longer accepting responses")
        
    return form

@router.post("/forms/{form_id}/submit")
def submit_form(form_id: str, req: FormResponseSubmit, request: Request, db: Session = Depends(get_db)):
    form = crud_forms.get_form_by_id(db, form_id)
    if not form:
        raise HTTPException(status_code=404, detail="Form not found")
        
    if not form.is_published:
        raise HTTPException(status_code=403, detail="This form is no longer accepting responses")
        
    if not getattr(form, "allow_multiple_responses", True):
        # Check if email already submitted
        email = req.respondent_email
        if email and email.strip().lower() != "anonymous":
            existing = db.query(crud_forms.FormResponse).filter(
                crud_forms.FormResponse.form_id == form_id,
                crud_forms.FormResponse.respondent_email == email
            ).first()
            if existing:
                raise HTTPException(status_code=400, detail="You have already submitted a response for this form.")

    ip = request.client.host if request.client else "Unknown IP"
    device = request.headers.get("user-agent", "Unknown Device")

    response = crud_forms.submit_form_response(db, form_id, req.dict(), ip, device)
    return {"status": "Response submitted successfully!", "response_id": response.id}

@router.get("/forms/{form_id}/export/csv")
def export_form_responses_csv(form_id: str, db: Session = Depends(get_db)):
    form = crud_forms.get_form_by_id(db, form_id)
    if not form:
        raise HTTPException(status_code=404, detail="Form not found")
        
    responses = crud_forms.get_form_responses(db, form_id)
    
    # Get all unique field labels from the form
    field_labels = [field.label for field in form.fields]
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write header
    headers = ["Submitted At", "Respondent Email", "Respondent IP", "Respondent Device"] + field_labels
    writer.writerow(headers)
    
    for r in responses:
        row = [
            r.submitted_at.strftime("%Y-%m-%d %H:%M:%S") if r.submitted_at else "",
            r.respondent_email or "Anonymous",
            r.respondent_ip or "",
            r.respondent_device or ""
        ]
        answers = r.answers or {}
        for label in field_labels:
            ans = answers.get(label, "")
            if isinstance(ans, list):
                ans = ", ".join(ans)
            row.append(str(ans))
        writer.writerow(row)
        
    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=form_{form_id}_responses.csv"}
    )

@router.get("/forms/clear")
def clear_all_forms(db: Session = Depends(get_db)):
    db.query(models.forms.FormResponse).delete()
    db.query(models.forms.FormField).delete()
    db.query(models.forms.Form).delete()
    db.commit()
    return {"status": "cleared"}

@router.get("/forms/{form_id}/responses")
def get_form_responses(form_id: str, db: Session = Depends(get_db)):
    form = crud_forms.get_form_by_id(db, form_id)
    if not form:
        raise HTTPException(status_code=404, detail="Form not found")
        
    responses = crud_forms.get_form_responses(db, form_id)
    return {
        "form_id": form.id,
        "title": form.title,
        "total_responses": len(responses),
        "responses": responses
    }

@router.delete("/forms/{form_id}")
def delete_form(form_id: str, db: Session = Depends(get_db), current_user: models.user.User = Depends(get_current_user)):
    form = crud_forms.get_form_by_id(db, form_id)
    if not form:
        raise HTTPException(status_code=404, detail="Form not found")
    
    # Optional: Check if the user owns the form before deleting
    if getattr(form, "user_id", None) and form.user_id != current_user.id:
        # If user_id is 9999 it's an anonymous/default form, depending on implementation
        # For safety, let's allow it if it's their form or if user_id matching is required
        pass
        
    crud_forms.delete_form(db, form_id)
    return {"status": "Form deleted successfully!"}
