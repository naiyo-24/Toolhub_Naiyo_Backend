from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Boolean
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from database import Base

class Organization(Base):
    __tablename__ = "organizations"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    organization_type = Column(String, nullable=True)
    branch_name = Column(String, nullable=True)
    branch_code = Column(String, nullable=True)
    city = Column(String, nullable=True)
    state = Column(String, nullable=True)
    office_contact = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class BankerOrganization(Base):
    __tablename__ = "banker_organizations"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"), index=True)
    is_primary = Column(Boolean, default=False)
    joined_at = Column(DateTime(timezone=True), server_default=func.now())

    organization = relationship("Organization")
