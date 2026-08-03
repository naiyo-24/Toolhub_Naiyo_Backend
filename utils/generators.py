import qrcode
from io import BytesIO
import barcode
from barcode.writer import ImageWriter
import random
import string
import re
import requests
from PIL import Image

def format_qr_data(qr_type: str, data: str, qr_data: dict) -> str:
    """Formats payload string based on QR type"""
    qr_type = qr_type.lower()
    
    # 1. Plain Text / Basic URLs
    if qr_type in ["text", "url", "website", "pdf", "social", "app", "meet", "zoom", "custom"]:
        return data or ""
    
    # 2. Communications
    if qr_type == "phone":
        return f"tel:{qr_data.get('number', '')}"
    if qr_type == "sms":
        return f"smsto:{qr_data.get('number', '')}:{qr_data.get('message', '')}"
    if qr_type == "whatsapp":
        return f"https://wa.me/{qr_data.get('number', '')}?text={qr_data.get('message', '')}"
    if qr_type == "email":
        return f"MATMSG:TO:{qr_data.get('email', '')};SUB:{qr_data.get('subject', '')};BODY:{qr_data.get('body', '')};;"
    
    # 3. Advanced
    if qr_type == "wifi":
        return f"WIFI:T:{qr_data.get('encryption', 'WPA')};S:{qr_data.get('ssid', '')};P:{qr_data.get('password', '')};;"
    
    if qr_type in ["vcard", "contact", "business_card"]:
        vcard = "BEGIN:VCARD\nVERSION:3.0\n"
        vcard += f"FN:{qr_data.get('name', '')}\n"
        vcard += f"TEL:{qr_data.get('phone', '')}\n"
        vcard += f"EMAIL:{qr_data.get('email', '')}\n"
        vcard += f"URL:{qr_data.get('website', '')}\n"
        vcard += f"ORG:{qr_data.get('company', '')}\n"
        vcard += "END:VCARD"
        return vcard
        
    if qr_type == "location":
        return f"geo:{qr_data.get('lat', '')},{qr_data.get('lng', '')}"
        
    if qr_type == "calendar":
        return f"BEGIN:VEVENT\nSUMMARY:{qr_data.get('title', '')}\nLOCATION:{qr_data.get('location', '')}\nDESCRIPTION:{qr_data.get('description', '')}\nEND:VEVENT"
        
    if qr_type in ["upi", "gpay", "phonepe", "paytm"]:
        base_upi = f"upi://pay?pa={qr_data.get('vpa', '')}&pn={qr_data.get('name', '')}"
        if qr_data.get('amount'):
            base_upi += f"&am={qr_data['amount']}"
        return base_upi
        
    return data or ""

from PIL import Image, ImageOps

import base64
def generate_qr_code(data: str, fill_color: str, back_color: str, logo_url: str = None, logo_base64: str = None,
                     border_size: int = 4, border_color: str = None, border_width: int = 0):
    qr = qrcode.QRCode(
        version=None, # Auto size
        error_correction=qrcode.constants.ERROR_CORRECT_H if (logo_url or logo_base64) else qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=border_size,
    )
    qr.add_data(data)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color=fill_color, back_color=back_color).convert('RGBA')
    
    if logo_url or logo_base64:
        try:
            logo = None
            if logo_base64:
                if "," in logo_base64:
                    logo_base64 = logo_base64.split(",")[1]
                image_data = base64.b64decode(logo_base64)
                logo = Image.open(BytesIO(image_data)).convert("RGBA")
            elif logo_url:
                response = requests.get(logo_url)
                if response.status_code == 200:
                    logo = Image.open(BytesIO(response.content)).convert("RGBA")
            
            if logo:
                try:
                    logo = logo.convert("RGBA")
                    # Check if the image already has transparency. If so, don't try to remove background.
                    alpha = logo.getchannel("A")
                    extrema = alpha.getextrema()
                    # extrema[0] is the minimum alpha value. If it's less than 255, there is transparency.
                    if extrema[0] == 255:
                        datas = logo.getdata()
                        new_data = []
                        # Sample top-left corner for background color
                        bg_color = datas[0]
                        tolerance = 30
                        
                        for item in datas:
                            # Only remove if it matches RGB exactly within tolerance, and is currently opaque
                            if (abs(item[0] - bg_color[0]) <= tolerance and 
                                abs(item[1] - bg_color[1]) <= tolerance and 
                                abs(item[2] - bg_color[2]) <= tolerance):
                                new_data.append((255, 255, 255, 0)) # transparent
                            else:
                                new_data.append(item)
                                
                        logo.putdata(new_data)
                except Exception as e:
                    print(f"Background removal error: {e}")

                # Calculate logo size (max 25% of QR code width/height)
                basewidth = int(img.size[0] * 0.25)
                wpercent = (basewidth/float(logo.size[0]))
                hsize = int((float(logo.size[1])*float(wpercent)))
                logo = logo.resize((basewidth, hsize), Image.Resampling.LANCZOS)
                
                # Position logo in center
                pos = ((img.size[0] - logo.size[0]) // 2, (img.size[1] - logo.size[1]) // 2)
                img.paste(logo, pos, logo)
        except Exception as e:
            print(f"Error loading logo: {e}")
            pass # Fallback to normal QR if logo fails
            
    if border_width > 0 and border_color:
        try:
            img = ImageOps.expand(img, border=border_width, fill=border_color)
        except Exception as e:
            print(f"Error adding border: {e}")
            
    buf = BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf


def generate_barcode(data: str, barcode_type: str):
    barcode_mapping = {
        "product": "ean13",
        "inventory": "code128",
        "shipping": "gs1_128",
        "asset": "code39",
        "ticket": "code128",
        "medical": "codabar",
        "library": "codabar",
        "small_product": "ean8",
        "retail_usa": "upca",
        "custom": "code128" # Default for custom if not specified
    }
    
    tech_type = barcode_mapping.get(barcode_type.lower(), barcode_type.lower())
    
    # EAN/UPC variants require numeric data only and specific lengths.
    # Fallback to code128 if the data is fundamentally incompatible with the strict numeric types.
    if tech_type in ('ean13', 'ean8', 'upca', 'ean') and not data.isdigit():
        tech_type = 'code128'
        
    try:
        BARCODE = barcode.get_barcode_class(tech_type)
    except barcode.errors.BarcodeNotFoundError:
        BARCODE = barcode.get_barcode_class('code128')
        
    bc = BARCODE(data, writer=ImageWriter())
    buf = BytesIO()
    bc.write(buf)
    buf.seek(0)
    return buf

def generate_password(length: int, upper: bool, lower: bool, nums: bool, syms: bool, custom_chars: str = None):
    import secrets
    chars = ""
    
    if upper: chars += string.ascii_uppercase
    if lower: chars += string.ascii_lowercase
    if nums: chars += string.digits
    if syms: chars += "!@#$%^&*_+-=" # User-friendly and universally accepted symbols
    
    if custom_chars:
        # Append custom characters instead of overriding everything
        chars += custom_chars
        
    if not chars:
        chars = string.ascii_letters + string.digits
            
    # Ensure length is respected even with a custom pool
    return ''.join(secrets.choice(chars) for _ in range(length))

def check_password_strength(password: str):
    score = 0
    feedback = []
    
    if len(password) >= 8: score += 1
    else: feedback.append("Make it at least 8 characters.")
    
    if re.search(r"[A-Z]", password) and re.search(r"[a-z]", password): score += 1
    else: feedback.append("Mix upper and lowercase letters.")
    
    if re.search(r"\d", password): score += 1
    else: feedback.append("Add some numbers.")
    
    if re.search(r"[!@#$%^&*(),.?\":{}|<>]", password): score += 1
    else: feedback.append("Include special symbols.")
    
    if score == 4 and len(password) >= 12:
        return 4, "Strong password."
    elif score >= 3:
        return 3, "Good password. " + " ".join(feedback)
    elif score >= 2:
        return 2, "Weak password. " + " ".join(feedback)
    else:
        return 1, "Very weak password. " + " ".join(feedback)
