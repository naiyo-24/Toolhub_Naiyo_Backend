from fastapi import APIRouter, File, UploadFile, HTTPException
from fastapi.responses import StreamingResponse
from PIL import Image
import io

from schemas.daily_utility import *
from utils import calculators, generators

router = APIRouter(
    prefix="/daily-utility",
    tags=["Daily Utility"]
)

# ---------------------------------------------------------
# GENERATORS & SCANNERS
# ---------------------------------------------------------

@router.post("/qr/generate")
def generate_qr(req: QRGenRequest):
    # Format the payload based on the requested QR type
    formatted_data = generators.format_qr_data(req.qr_type, req.data, req.qr_data or {})
    
    # Generate the image
    buf = generators.generate_qr_code(
        data=formatted_data, 
        fill_color=req.fill_color, 
        back_color=req.back_color,
        logo_url=req.logo_url,
        logo_base64=req.logo_base64,
        border_size=req.border_size,
        border_color=req.border_color,
        border_width=req.border_width
    )
    return StreamingResponse(buf, media_type="image/png")

@router.post("/qr/scan")
async def scan_qr(file: UploadFile = File(...)):
    try:
        import cv2
        import numpy as np
        
        contents = await file.read()
        nparr = np.frombuffer(contents, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        detector = cv2.QRCodeDetector()
        data, bbox, straight_qrcode = detector.detectAndDecode(img)
        
        if not data:
            return {"data": None, "message": "No QR code found. (Note: Barcodes require a separate detector)"}
            
        return {"data": data, "type": "QRCODE"}
    except ImportError:
        raise HTTPException(status_code=500, detail="Server missing opencv-python-headless dependency.")
    except Exception as e:
        raise HTTPException(status_code=400, detail="Invalid image file.")

@router.post("/barcode/generate")
def generate_barcode(req: BarcodeGenRequest):
    buf = generators.generate_barcode(req.data, req.barcode_type)
    return StreamingResponse(buf, media_type="image/png")

@router.post("/barcode/scan")
async def scan_barcode(file: UploadFile = File(...)):
    try:
        import zxingcpp
        from PIL import Image
        import io
        
        contents = await file.read()
        image = Image.open(io.BytesIO(contents))
        
        results = zxingcpp.read_barcodes(image)
        
        if not results:
            return {"data": None, "message": "No barcode found in the image."}
            
        return {"data": results[0].text, "type": results[0].format.name}
    except ImportError:
        raise HTTPException(status_code=500, detail="Server missing zxing-cpp dependency.")
    except Exception as e:
        raise HTTPException(status_code=400, detail="Invalid image file.")

@router.post("/password/generate")
def generate_password(req: PasswordGenRequest):
    pwd = generators.generate_password(
        req.length, req.include_uppercase, req.include_lowercase, 
        req.include_numbers, req.include_symbols, req.custom_chars
    )
    return {"password": pwd}

@router.post("/password/check", response_model=PasswordCheckResponse)
def check_password(req: PasswordCheckRequest):
    score, feedback = generators.check_password_strength(req.password)
    return {"score": score, "feedback": feedback}

# ---------------------------------------------------------
# CALCULATORS (Financial)
# ---------------------------------------------------------

@router.post("/emi", response_model=EMICalcResponse)
def calculate_emi(req: EMICalcRequest):
    return calculators.calculate_emi(req.principal, req.annual_rate, req.tenure_months)

@router.post("/gst", response_model=GSTCalcResponse)
def calculate_gst(req: GSTCalcRequest):
    return calculators.calculate_gst(req.amount, req.gst_rate, req.is_inclusive)

@router.post("/sip", response_model=SIPCalcResponse)
def calculate_sip(req: SIPCalcRequest):
    return calculators.calculate_sip(req.monthly_investment, req.expected_annual_return, req.tenure_years)

@router.post("/loan", response_model=EMICalcResponse)
def calculate_loan(req: EMICalcRequest):
    # Loan calculation is mathematically identical to EMI
    return calculators.calculate_emi(req.principal, req.annual_rate, req.tenure_months)

@router.post("/discount", response_model=DiscountCalcResponse)
def calculate_discount(req: DiscountCalcRequest):
    discount_amount = req.original_price * (req.discount_percentage / 100)
    final_price = req.original_price - discount_amount
    return {"discount_amount": round(discount_amount, 2), "final_price": round(final_price, 2)}

# ---------------------------------------------------------
# CALCULATORS (Health & Math)
# ---------------------------------------------------------

@router.post("/age", response_model=AgeCalcResponse)
def calculate_age(req: AgeCalcRequest):
    return calculators.calculate_age(req.birth_date)

@router.post("/bmi", response_model=BMICalcResponse)
def calculate_bmi(req: BMICalcRequest):
    return calculators.calculate_bmi(req.weight_kg, req.height_cm, req.age)

@router.post("/percentage")
def calculate_percentage(part: float, total: float):
    if total == 0:
        raise HTTPException(status_code=400, detail="Total cannot be zero.")
    return {"percentage": round((part / total) * 100, 2)}

@router.post("/convert/unit")
def convert_unit(value: float, from_unit: str, to_unit: str):
    try:
        converted = calculators.convert_unit(value, from_unit, to_unit)
        return {"converted_value": converted, "message": f"Successfully converted {value} {from_unit} to {converted} {to_unit}"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/convert/currency")
def convert_currency(amount: float, from_currency: CurrencyCode, to_currency: CurrencyCode):
    try:
        converted = calculators.convert_currency(amount, from_currency, to_currency)
        return {"converted_amount": converted, "message": f"Successfully converted {amount} {from_currency.upper()} to {converted} {to_currency.upper()}"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/convert/bindec", response_model=BinDecResponse)
def convert_bindec(req: BinDecRequest):
    try:
        decimal_val = int(req.value, req.from_base)
        if req.to_base == 2:
            converted = bin(decimal_val)[2:]
        elif req.to_base == 10:
            converted = str(decimal_val)
        elif req.to_base == 16:
            converted = hex(decimal_val)[2:]
        else:
            raise ValueError
        return {"converted_value": converted}
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid input for the specified base.")

# ---------------------------------------------------------
# STRING TOOLS
# ---------------------------------------------------------

@router.post("/text/counter", response_model=TextCounterResponse)
def count_text(req: TextCounterRequest):
    return calculators.analyze_text(req.text)

@router.post("/text/case", response_model=CaseConvertResponse)
def convert_case(req: CaseConvertRequest):
    converted = calculators.convert_case(req.text, req.case_type)
    return {"converted_text": converted}
