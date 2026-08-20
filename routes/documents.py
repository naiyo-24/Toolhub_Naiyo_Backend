from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from database import get_db
from models.user import User
from models.loan_case import LoanCase
from models.document import Document, DocumentVersion
from schemas.document import DocumentResponse, DocumentAccessResponse
from routes.auth import get_current_user
from utils.storage import generate_storage_key, save_upload_file, get_file_hash
import os

router = APIRouter()

@router.get("/case/{case_id}", response_model=list[DocumentResponse])
def get_case_documents(case_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    loan_case = db.query(LoanCase).filter(LoanCase.id == case_id, LoanCase.banker_id == current_user.id).first()
    if not loan_case:
        raise HTTPException(status_code=404, detail="Case not found")
        
    documents = db.query(Document).filter(Document.case_id == case_id).all()
    return documents

@router.post("/upload", response_model=DocumentResponse)
def upload_document(
    case_id: int = Form(...),
    document_type: str = Form(...),
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user), 
    db: Session = Depends(get_db)
):
    loan_case = db.query(LoanCase).filter(LoanCase.id == case_id, LoanCase.banker_id == current_user.id).first()
    if not loan_case:
        raise HTTPException(status_code=404, detail="Case not found")

    storage_key = generate_storage_key(case_id, file.filename)
    file_path = save_upload_file(file, storage_key)
    file_hash = get_file_hash(file_path)
    file_size = os.path.getsize(file_path)

    # Check if document type already exists to create version
    existing_doc = db.query(Document).filter(Document.case_id == case_id, Document.document_type == document_type).first()
    
    if existing_doc:
        # Create new version
        version_count = db.query(DocumentVersion).filter(DocumentVersion.document_id == existing_doc.id).count()
        new_version = DocumentVersion(
            document_id=existing_doc.id,
            version_number=version_count + 1,
            storage_key=existing_doc.storage_key,
            file_name=existing_doc.file_name,
            file_size=existing_doc.file_size,
            file_hash=existing_doc.file_hash,
            created_by=existing_doc.created_by
        )
        db.add(new_version)
        
        # Update current doc
        existing_doc.file_name = file.filename
        existing_doc.mime_type = file.content_type
        existing_doc.file_size = file_size
        existing_doc.storage_key = storage_key
        existing_doc.file_hash = file_hash
        existing_doc.updated_by = current_user.id
        doc = existing_doc
    else:
        # Create new doc
        doc = Document(
            case_id=case_id,
            document_type=document_type,
            file_name=file.filename,
            mime_type=file.content_type,
            file_size=file_size,
            storage_key=storage_key,
            file_hash=file_hash,
            created_by=current_user.id
        )
        db.add(doc)

    db.commit()
    db.refresh(doc)
    return doc

@router.get("/{document_id}/access", response_model=DocumentAccessResponse)
def get_document_access(document_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
        
    loan_case = db.query(LoanCase).filter(LoanCase.id == doc.case_id, LoanCase.banker_id == current_user.id).first()
    if not loan_case:
        raise HTTPException(status_code=403, detail="Not authorized to access this document")
    
    # In a real cloud setup, this would generate a signed URL.
    # For local server setup, we return an authenticated download route.
    # The Flutter app must append the Bearer token to this URL when downloading/viewing.
    url = f"/api/v1/documents/download/{document_id}"
    
    return DocumentAccessResponse(
        document_id=doc.id,
        file_name=doc.file_name,
        url=url
    )

@router.get("/download/{document_id}")
def download_document(document_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
        
    loan_case = db.query(LoanCase).filter(LoanCase.id == doc.case_id, LoanCase.banker_id == current_user.id).first()
    if not loan_case:
        raise HTTPException(status_code=403, detail="Not authorized to access this document")
        
    file_path = os.path.join("uploads", doc.storage_key)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found on server")
        
    return FileResponse(file_path, filename=doc.file_name)
