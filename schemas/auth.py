from pydantic import BaseModel, field_validator, model_validator
from typing import Optional, Any

class GoogleLoginRequest(BaseModel):
    id_token: Optional[str] = None
    token: Optional[str] = None

class RefreshRequest(BaseModel):
    refresh_token: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    refresh_token: str = ""

class UserResponse(BaseModel):
    id: str
    google_id: str
    email: str
    full_name: str = ""
    profile_pic: str = ""
    company_name: str = ""
    company_logo_url: str = ""
    company_address: str = ""
    whatsapp_number: str = ""
    phone_number: str = ""
    gst_number: str = ""
    business_type: str = ""
    bank_name: str = ""
    account_name: str = ""
    account_number: str = ""
    ifsc_code: str = ""
    pricing_mode: str = ""
    created_at: Optional[Any] = None
    updated_at: Optional[Any] = None

    @model_validator(mode='before')
    @classmethod
    def coerce_data(cls, values):
        from pydantic import BaseModel
        # Convert SQLAlchemy object to dict if necessary
        if not isinstance(values, dict):
            # Extract attributes dynamically
            d = {}
            for attr in dir(values):
                if not attr.startswith('_'):
                    d[attr] = getattr(values, attr)
        else:
            d = dict(values)
            
        # Coerce None to "" and ints to strings for fields that require it
        for k, v in d.items():
            if v is None:
                if k in ['created_at', 'updated_at']:
                    d[k] = None
                else:
                    d[k] = ""
            elif isinstance(v, int):
                d[k] = str(v)
            elif k in ['created_at', 'updated_at'] and hasattr(v, 'isoformat'):
                d[k] = v.isoformat()
        return d

    class Config:
        from_attributes = True

class AuthResponse(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse
    refresh_token: str = ""

class ProfileUpdateRequest(BaseModel):
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

class DeleteAccountRequest(BaseModel):
    email: str
    reason: Optional[str] = None
