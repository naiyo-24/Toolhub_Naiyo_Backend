from sqlalchemy.orm import Session, joinedload
from models.forms import Form, FormField, FormResponse
import uuid

def create_form(db: Session, form_data: dict, fields_data: list, user_id: int = 9999):
    db_form = Form(
        title=form_data["title"],
        description=form_data.get("description"),
        header_image_url=form_data.get("header_image_url"),
        form_type=form_data.get("form_type"),
        is_published=form_data.get("is_published", True),
        user_id=user_id
    )
    db.add(db_form)
    db.commit()
    db.refresh(db_form)
    
    for f in fields_data:
        db_field = FormField(
            form_id=db_form.id,
            label=f["label"],
            field_type=f["field_type"],
            is_required=f.get("is_required", False),
            options=f.get("options"),
            order_index=f.get("order_index", 0)
        )
        db.add(db_field)
    
    db.commit()
    db.refresh(db_form)
    return db_form

def get_form_by_id(db: Session, form_id: str):
    return db.query(Form).options(joinedload(Form.fields)).filter(Form.id == form_id).first()

def get_user_forms(db: Session, user_id: int = 9999):
    return db.query(Form).options(joinedload(Form.fields)).filter(Form.user_id == user_id).order_by(Form.created_at.desc()).all()

def submit_form_response(db: Session, form_id: str, response_data: dict, ip: str = None, device: str = None):
    db_response = FormResponse(
        form_id=form_id,
        respondent_email=response_data.get("respondent_email"),
        respondent_ip=ip,
        respondent_device=device,
        answers=response_data["answers"]
    )
    db.add(db_response)
    db.commit()
    db.refresh(db_response)
    return db_response

def get_form_responses(db: Session, form_id: str):
    return db.query(FormResponse).filter(FormResponse.form_id == form_id).order_by(FormResponse.submitted_at.desc()).all()

def update_form(db: Session, form_id: str, form_data: dict, fields_data: list):
    db_form = get_form_by_id(db, form_id)
    if not db_form:
        return None
        
    db_form.title = form_data.get("title", db_form.title)
    db_form.description = form_data.get("description", db_form.description)
    db_form.header_image_url = form_data.get("header_image_url", db_form.header_image_url)
    db_form.form_type = form_data.get("form_type", db_form.form_type)
    db_form.is_published = form_data.get("is_published", db_form.is_published)
    
    # Delete existing fields
    db.query(FormField).filter(FormField.form_id == form_id).delete()
    
    # Recreate fields
    for f in fields_data:
        db_field = FormField(
            form_id=db_form.id,
            label=f["label"],
            field_type=f["field_type"],
            is_required=f.get("is_required", False),
            options=f.get("options"),
            order_index=f.get("order_index", 0)
        )
        db.add(db_field)
        
    db.commit()
    db.refresh(db_form)
    return db_form

def delete_form(db: Session, form_id: str):
    # Delete responses first to avoid foreign key constraints
    db.query(FormResponse).filter(FormResponse.form_id == form_id).delete()
    # Delete fields
    db.query(FormField).filter(FormField.form_id == form_id).delete()
    # Delete the form itself
    db.query(Form).filter(Form.id == form_id).delete()
    db.commit()
    return True
