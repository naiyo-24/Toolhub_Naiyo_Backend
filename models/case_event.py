from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from database import Base

class CaseEvent(Base):
    __tablename__ = "case_events"

    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, ForeignKey("loan_cases.id"), nullable=False, index=True)

    event_type = Column(String, nullable=False) # e.g. STATUS_CHANGE, DOCUMENT_UPLOADED, TASK_COMPLETED
    description = Column(Text, nullable=False)

    actor_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    case = relationship("LoanCase")
    actor = relationship("User")
