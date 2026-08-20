from sqlalchemy import Column, Integer, String, BigInteger, ForeignKey, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from database import Base

class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, ForeignKey("loan_cases.id"), index=True, nullable=False)
    
    document_type = Column(String, nullable=False, index=True)
    file_name = Column(String, nullable=False)
    mime_type = Column(String, nullable=True)

    file_size = Column(BigInteger, nullable=True)
    page_count = Column(Integer, nullable=True)

    storage_type = Column(String, default="LOCAL")
    storage_key = Column(String, nullable=False)

    file_hash = Column(String(64), nullable=True, index=True)

    ocr_status = Column(String, nullable=True)
    verification_status = Column(String, nullable=True)
    document_status = Column(String, nullable=True)

    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    case = relationship("LoanCase")
    creator = relationship("User")

class DocumentVersion(Base):
    __tablename__ = "document_versions"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"), index=True, nullable=False)
    
    version_number = Column(Integer, nullable=False)
    
    storage_key = Column(String, nullable=False)
    file_name = Column(String, nullable=False)
    file_size = Column(BigInteger, nullable=True)
    file_hash = Column(String(64), nullable=True)

    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    document = relationship("Document")
