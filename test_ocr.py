from database import SessionLocal
import models.loan_case
from models.document import Document
from routes.ocr import run_ocr_on_document
from models.user import User

db = SessionLocal()
doc = db.query(Document).filter(Document.document_type == "Bank Statement").order_by(Document.id.desc()).first()

if not doc:
    print("No bank statement found")
else:
    print(f"Running OCR on doc_id {doc.id}")
    try:
        mock_user = User(id=1, email="test@test.com")
        res = run_ocr_on_document(doc.id, current_user=mock_user, db=db)
        print("SUCCESS!")
    except Exception as e:
        print(f"ERROR: {e}")
