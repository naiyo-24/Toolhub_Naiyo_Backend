from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import date, datetime
from enum import Enum

class CurrencyCode(str, Enum):
    USD = "USD"
    EUR = "EUR"
    GBP = "GBP"
    INR = "INR"
    AUD = "AUD"
    CAD = "CAD"
    SGD = "SGD"
    CHF = "CHF"
    MYR = "MYR"
    JPY = "JPY"
    CNY = "CNY"
    AED = "AED"
    AFN = "AFN"
    ALL = "ALL"
    AMD = "AMD"
    ANG = "ANG"
    AOA = "AOA"
    ARS = "ARS"
    AWG = "AWG"
    AZN = "AZN"
    BAM = "BAM"
    BBD = "BBD"
    BDT = "BDT"
    BGN = "BGN"
    BHD = "BHD"
    BIF = "BIF"
    BMD = "BMD"
    BND = "BND"
    BOB = "BOB"
    BRL = "BRL"
    BSD = "BSD"
    BTN = "BTN"
    BWP = "BWP"
    BYN = "BYN"
    BZD = "BZD"
    CDF = "CDF"
    CLP = "CLP"
    COP = "COP"
    CRC = "CRC"
    CUP = "CUP"
    CVE = "CVE"
    CZK = "CZK"
    DJF = "DJF"
    DKK = "DKK"
    DOP = "DOP"
    DZD = "DZD"
    EGP = "EGP"
    ERN = "ERN"
    ETB = "ETB"
    FJD = "FJD"
    FKP = "FKP"
    FOK = "FOK"
    GEL = "GEL"
    GGP = "GGP"
    GHS = "GHS"
    GIP = "GIP"
    GMD = "GMD"
    GNF = "GNF"
    GTQ = "GTQ"
    GYD = "GYD"
    HKD = "HKD"
    HNL = "HNL"
    HRK = "HRK"
    HTG = "HTG"
    HUF = "HUF"
    IDR = "IDR"
    ILS = "ILS"
    IMP = "IMP"
    IQD = "IQD"
    IRR = "IRR"
    ISK = "ISK"
    JEP = "JEP"
    JMD = "JMD"
    JOD = "JOD"
    KES = "KES"
    KGS = "KGS"
    KHR = "KHR"
    KID = "KID"
    KMF = "KMF"
    KRW = "KRW"
    KWD = "KWD"
    KYD = "KYD"
    KZT = "KZT"
    LAK = "LAK"
    LBP = "LBP"
    LKR = "LKR"
    LRD = "LRD"
    LSL = "LSL"
    LYD = "LYD"
    MAD = "MAD"
    MDL = "MDL"
    MGA = "MGA"
    MKD = "MKD"
    MMK = "MMK"
    MNT = "MNT"
    MOP = "MOP"
    MRU = "MRU"
    MUR = "MUR"
    MVR = "MVR"
    MWK = "MWK"
    MXN = "MXN"
    MZN = "MZN"
    NAD = "NAD"
    NGN = "NGN"
    NIO = "NIO"
    NOK = "NOK"
    NPR = "NPR"
    NZD = "NZD"
    OMR = "OMR"
    PAB = "PAB"
    PEN = "PEN"
    PGK = "PGK"
    PHP = "PHP"
    PKR = "PKR"
    PLN = "PLN"
    PYG = "PYG"
    QAR = "QAR"
    RON = "RON"
    RSD = "RSD"
    RUB = "RUB"
    RWF = "RWF"
    SAR = "SAR"
    SBD = "SBD"
    SCR = "SCR"
    SDG = "SDG"
    SEK = "SEK"
    SHP = "SHP"
    SLE = "SLE"
    SLL = "SLL"
    SOS = "SOS"
    SRD = "SRD"
    SSP = "SSP"
    STN = "STN"
    SYP = "SYP"
    SZL = "SZL"
    THB = "THB"
    TJS = "TJS"
    TMT = "TMT"
    TND = "TND"
    TOP = "TOP"
    TRY = "TRY"
    TTD = "TTD"
    TVD = "TVD"
    TWD = "TWD"
    TZS = "TZS"
    UAH = "UAH"
    UGX = "UGX"
    UYU = "UYU"
    UZS = "UZS"
    VES = "VES"
    VND = "VND"
    VUV = "VUV"
    WST = "WST"
    XAF = "XAF"
    XCD = "XCD"
    XDR = "XDR"
    XOF = "XOF"
    XPF = "XPF"
    YER = "YER"
    ZAR = "ZAR"
    ZMW = "ZMW"
    ZWL = "ZWL"
class QRGenRequest(BaseModel):
    qr_type: str = "text" # 'text', 'url', 'wifi', 'vcard', etc.
    data: Optional[str] = None
    qr_data: Optional[dict] = None
    logo_url: Optional[str] = None # For custom logo in the center
    logo_base64: Optional[str] = None # For base64 encoded custom logo
    fill_color: str = "black"
    back_color: str = "white"
    border_color: str = "black" # Color of the outer frame border
    border_size: int = 4 # Quiet zone thickness (blocks)
    border_width: int = 0 # Thickness of the outer frame border (pixels)

class BarcodeGenRequest(BaseModel):
    data: str
    barcode_type: str = "product" # product, inventory, shipping, asset, ticket, medical, library, small_product, retail_usa, custom

class PasswordGenRequest(BaseModel):
    length: int = Field(default=12, ge=4, le=128)
    include_uppercase: bool = True
    include_lowercase: bool = True
    include_numbers: bool = True
    include_symbols: bool = True
    custom_chars: Optional[str] = None

class PasswordCheckRequest(BaseModel):
    password: str

class PasswordCheckResponse(BaseModel):
    score: int # 0 to 4
    feedback: str

class EMICalcRequest(BaseModel):
    principal: float
    annual_rate: float
    tenure_months: int

class EMICalcResponse(BaseModel):
    emi: float
    total_interest: float
    total_payment: float

class GSTCalcRequest(BaseModel):
    amount: float
    gst_rate: float
    is_inclusive: bool = False

class GSTCalcResponse(BaseModel):
    net_amount: float
    gst_amount: float
    total_amount: float

class AgeCalcRequest(BaseModel):
    birth_date: date

class AgeCalcResponse(BaseModel):
    years: int
    months: int
    days: int
    total_days: int

class SIPCalcRequest(BaseModel):
    monthly_investment: float
    expected_annual_return: float
    tenure_years: int

class SIPCalcResponse(BaseModel):
    invested_amount: float
    estimated_returns: float
    total_value: float

class DiscountCalcRequest(BaseModel):
    original_price: float
    discount_percentage: float

class DiscountCalcResponse(BaseModel):
    discount_amount: float
    final_price: float

class BMICalcRequest(BaseModel):
    weight_kg: float
    height_cm: float
    age: int | None = None

class BMICalcResponse(BaseModel):
    bmi: float
    category: str

class TextCounterRequest(BaseModel):
    text: str

class TextCounterResponse(BaseModel):
    characters: int
    words: int
    lines: int
    spaces: int

class CaseConvertRequest(BaseModel):
    text: str
    case_type: str # upper, lower, title, camel, snake, kebab

class CaseConvertResponse(BaseModel):
    converted_text: str

class BinDecRequest(BaseModel):
    value: str
    from_base: int = 10
    to_base: int = 2

class BinDecResponse(BaseModel):
    converted_value: str
