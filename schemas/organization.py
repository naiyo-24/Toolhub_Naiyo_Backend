from pydantic import BaseModel
from typing import Optional

class OrganizationBase(BaseModel):
    name: str
    organization_type: Optional[str] = None
    branch_name: Optional[str] = None
    branch_code: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    office_contact: Optional[str] = None

class OrganizationCreate(OrganizationBase):
    pass

class OrganizationUpdate(BaseModel):
    name: Optional[str] = None
    organization_type: Optional[str] = None
    branch_name: Optional[str] = None
    branch_code: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    office_contact: Optional[str] = None

class OrganizationResponse(OrganizationBase):
    id: int

    class Config:
        from_attributes = True

class BankerOrganizationResponse(BaseModel):
    id: int
    user_id: int
    organization_id: int
    is_primary: bool
    organization: OrganizationResponse

    class Config:
        from_attributes = True
