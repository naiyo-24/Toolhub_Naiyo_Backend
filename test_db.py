from database import SessionLocal
from models.document import Document

db = SessionLocal()
doc = db.query(Document).filter(Document.document_type == "GST").order_by(Document.id.desc()).first()
if doc:
    print(f"File: {doc.storage_key}, type: {doc.document_type}, name: {doc.file_name}")
else:
    print("No GST doc found!")
