from pydantic import BaseModel, HttpUrl, EmailStr, validator
from typing import Optional, Dict, Any

class URLShortenRequest(BaseModel):
    url: HttpUrl
    
class URLShortenResponse(BaseModel):
    short_url: str
    original_url: str

class URLExpandRequest(BaseModel):
    short_url: HttpUrl

class LinkCheckRequest(BaseModel):
    url: HttpUrl

class EmailValidateRequest(BaseModel):
    email: EmailStr

class StatusCheckRequest(BaseModel):
    url: HttpUrl

class DNSLookupRequest(BaseModel):
    domain: str

class PingRequest(BaseModel):
    host: str

class JSONFormatRequest(BaseModel):
    json_string: str

class Base64ProcessRequest(BaseModel):
    text: str
    action: str # 'encode' or 'decode'

class WiFiQRRequest(BaseModel):
    ssid: str
    password: str
    encryption: str = "WPA"
    fill_color: str = "black"
    back_color: str = "white"

class UPIQRRequest(BaseModel):
    vpa: str
    name: str
    amount: Optional[str] = None
    fill_color: str = "black"
    back_color: str = "white"
