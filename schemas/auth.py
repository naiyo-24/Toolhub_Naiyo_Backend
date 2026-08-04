from pydantic import BaseModel
from typing import Optional

class GoogleLoginRequest(BaseModel):
    id_token: str

class UserResponse(BaseModel):
    id: int
    google_id: str
    email: str
    full_name: Optional[str] = None
    profile_pic: Optional[str] = None
    company_name: Optional[str] = None
    company_logo_url: Optional[str] = None
    company_address: Optional[str] = None
    whatsapp_number: Optional[str] = None
    phone_number: Optional[str] = None
    gst_number: Optional[str] = None
    business_type: Optional[str] = None
    bank_name: Optional[str] = None
    account_name: Optional[str] = None
    account_number: Optional[str] = None
    ifsc_code: Optional[str] = None
    pricing_mode: Optional[str] = None

    class Config:
        from_attributes = True

class AuthResponse(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse

class ProfileUpdateRequest(BaseModel):
    company_name: Optional[str] = None
    company_logo_url: Optional[str] = None
    company_address: Optional[str] = None
    whatsapp_number: Optional[str] = None
    phone_number: str
    gst_number: Optional[str] = None
    business_type: Optional[str] = None
    bank_name: Optional[str] = None
    account_name: Optional[str] = None
    account_number: Optional[str] = None
    ifsc_code: Optional[str] = None
    pricing_mode: Optional[str] = None

class DeleteAccountRequest(BaseModel):
    email: str
    reason: Optional[str] = None
