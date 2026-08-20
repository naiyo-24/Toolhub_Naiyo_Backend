from pydantic import BaseModel, model_validator
from typing import Optional
from datetime import date

class CustomerBase(BaseModel):
    customer_type: str = "Individual"
    full_name: str
    mobile: str
    email: Optional[str] = None

    @model_validator(mode='before')
    @classmethod
    def map_fields(cls, values):
        # When serializing a database object, 'values' is not a dictionary. Skip mapping.
        if not isinstance(values, dict):
            return values
            
        # Map 'name' from Flutter to 'full_name' in backend
        if 'name' in values and 'full_name' not in values:
            values['full_name'] = values['name']
        # Map 'phone' from Flutter to 'mobile' in backend
        if 'phone' in values and 'mobile' not in values:
            values['mobile'] = str(values['phone'])
        # Provide default customer_type if missing
        if 'customer_type' not in values:
            values['customer_type'] = "Individual"
        
        # Handle DD/MM/YYYY to YYYY-MM-DD conversion for dob
        if 'dob' in values and isinstance(values['dob'], str):
            dob_str = values['dob']
            if '/' in dob_str:
                parts = dob_str.split('/')
                # Assuming DD/MM/YYYY format based on input: 22/06/2004
                if len(parts) == 3:
                    values['dob'] = f"{parts[2]}-{parts[1]}-{parts[0]}"

        return values
    pan: Optional[str] = None
    dob: Optional[date] = None
    occupation: Optional[str] = None
    address: Optional[str] = None
    legal_name: Optional[str] = None
    business_name: Optional[str] = None
    business_type: Optional[str] = None
    gstin: Optional[str] = None
    udyam_number: Optional[str] = None

class CustomerCreate(CustomerBase):
    pass

class CustomerUpdate(BaseModel):
    customer_type: Optional[str] = None
    full_name: Optional[str] = None
    mobile: Optional[str] = None
    email: Optional[str] = None
    pan: Optional[str] = None
    dob: Optional[date] = None
    occupation: Optional[str] = None
    address: Optional[str] = None
    legal_name: Optional[str] = None
    business_name: Optional[str] = None
    business_type: Optional[str] = None
    gstin: Optional[str] = None
    udyam_number: Optional[str] = None

class CustomerResponse(CustomerBase):
    id: int
    created_by: int

    class Config:
        from_attributes = True
