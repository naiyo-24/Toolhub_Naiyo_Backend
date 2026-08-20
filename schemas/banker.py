from pydantic import BaseModel
from typing import Optional, List

class BankerProfileBase(BaseModel):
    mobile: Optional[str] = None
    role: Optional[str] = None
    designation: Optional[str] = None
    employee_id: Optional[str] = None
    experience_years: Optional[int] = None
    org_type: Optional[str] = None
    org_name: Optional[str] = None
    branch_name: Optional[str] = None
    city: Optional[str] = None
    state_region: Optional[str] = None
    loan_types: Optional[List[str]] = None

class BankerProfileCreate(BankerProfileBase):
    pass

class BankerProfileUpdate(BankerProfileBase):
    pass

class BankerProfileResponse(BankerProfileBase):
    id: int
    user_id: int

    class Config:
        from_attributes = True

class BankerLoanPreferenceBase(BaseModel):
    loan_type: str

class BankerLoanPreferenceResponse(BankerLoanPreferenceBase):
    id: int
    user_id: int

    class Config:
        from_attributes = True
