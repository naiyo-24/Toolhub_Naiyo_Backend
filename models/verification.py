from sqlalchemy import Column, Integer, String, Text, Boolean, ForeignKey, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from database import Base

class Verification(Base):
    __tablename__ = "verifications"

    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, ForeignKey("loan_cases.id"), nullable=False, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=True, index=True)

    verification_type = Column(String, nullable=False) # e.g. PAN, GST, UDYAM
    status = Column(String, nullable=False, default="NOT_CHECKED") # PENDING, VERIFIED, FAILED, MANUAL_REVIEW

    source = Column(String, nullable=True)
    reference_number = Column(String, nullable=True)

    verified_name = Column(String, nullable=True)
    verified_address = Column(Text, nullable=True)
    remarks = Column(Text, nullable=True)

    verified_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    verified_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    case = relationship("LoanCase")
    document = relationship("Document")
    verifier = relationship("User")

class CaseDocumentRequirement(Base):
    __tablename__ = "case_document_requirements"

    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, ForeignKey("loan_cases.id"), nullable=False, index=True)
    document_type = Column(String, nullable=False)

    is_required = Column(Boolean, default=True)
    status = Column(String, nullable=False, default="MISSING") # REQUIRED, MISSING, RECEIVED, VERIFIED

    received_at = Column(DateTime(timezone=True), nullable=True)
    verified_at = Column(DateTime(timezone=True), nullable=True)

    case = relationship("LoanCase")
