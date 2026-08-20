import os
import shutil
import hashlib
from fastapi import UploadFile

UPLOAD_DIR = "uploads/loandesk"
os.makedirs(UPLOAD_DIR, exist_ok=True)

def generate_storage_key(case_id: int, filename: str) -> str:
    # Example: loandesk/cases/1/documents/filename.pdf
    return f"loandesk/cases/{case_id}/documents/{filename}"

def save_upload_file(upload_file: UploadFile, storage_key: str) -> str:
    # Full path on local disk
    file_path = os.path.join("uploads", storage_key)
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(upload_file.file, buffer)
        
    return file_path

def get_file_hash(file_path: str) -> str:
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        # Read and update hash string value in blocks of 4K
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()
