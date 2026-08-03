from datetime import date
from dateutil.relativedelta import relativedelta
import re
import requests
def calculate_emi(principal: float, annual_rate: float, tenure_months: int):
    if annual_rate == 0:
        emi = principal / tenure_months
        return {"emi": round(emi, 2), "total_interest": 0, "total_payment": principal}
    
    monthly_rate = (annual_rate / 12) / 100
    emi = principal * monthly_rate * ((1 + monthly_rate)**tenure_months) / (((1 + monthly_rate)**tenure_months) - 1)
    total_payment = emi * tenure_months
    total_interest = total_payment - principal
    return {
        "emi": round(emi, 2),
        "total_interest": round(total_interest, 2),
        "total_payment": round(total_payment, 2)
    }

def calculate_gst(amount: float, gst_rate: float, is_inclusive: bool):
    if is_inclusive:
        base_amount = amount / (1 + (gst_rate / 100))
        gst_amount = amount - base_amount
        return {
            "net_amount": round(base_amount, 2),
            "gst_amount": round(gst_amount, 2),
            "total_amount": round(amount, 2)
        }
    else:
        gst_amount = amount * (gst_rate / 100)
        return {
            "net_amount": round(amount, 2),
            "gst_amount": round(gst_amount, 2),
            "total_amount": round(amount + gst_amount, 2)
        }

def calculate_age(birth_date: date):
    today = date.today()
    delta = relativedelta(today, birth_date)
    total_days = (today - birth_date).days
    return {
        "years": delta.years,
        "months": delta.months,
        "days": delta.days,
        "total_days": total_days
    }

def calculate_sip(monthly_investment: float, expected_annual_return: float, tenure_years: int):
    months = tenure_years * 12
    monthly_rate = (expected_annual_return / 12) / 100
    future_value = monthly_investment * (((1 + monthly_rate)**months - 1) / monthly_rate) * (1 + monthly_rate)
    invested_amount = monthly_investment * months
    return {
        "invested_amount": round(invested_amount, 2),
        "estimated_returns": round(future_value - invested_amount, 2),
        "total_value": round(future_value, 2)
    }

def calculate_bmi(weight_kg: float, height_cm: float, age: int = None):
    height_m = height_cm / 100
    bmi = weight_kg / (height_m * height_m)
    
    if bmi < 18.5:
        category = "Underweight"
    elif bmi < 25:
        category = "Normal"
    elif bmi < 30:
        category = "Overweight"
    else:
        category = "Obese"
        
    return {"bmi": round(bmi, 1), "category": category}

def analyze_text(text: str):
    words = len([w for w in text.split() if w.strip()])
    characters = len(text)
    spaces = text.count(" ")
    lines = len([s for s in text.split('.') if s.strip()])
    return {
        "characters": characters,
        "words": words,
        "lines": lines,
        "spaces": spaces
    }

def convert_case(text: str, case_type: str):
    case_type = case_type.lower().replace("case", "").strip()
    if case_type == "upper":
        return text.upper()
    elif case_type == "lower":
        return text.lower()
    elif case_type == "title":
        return text.title()
    
    # Clean up the text: replace dashes, underscores, and multiple spaces with a single space
    clean_text = re.sub(r'[^a-zA-Z0-9]+', ' ', text).strip()
    
    # Split based on spaces, or camelCase boundaries if it's a single word
    if ' ' not in clean_text:
        # It might already be camel/pascal case, split it up
        words = re.sub(r'([A-Z])', r' \1', clean_text).split()
    else:
        words = clean_text.split()
        
    if not words:
        return text

    if case_type == "camel":
        return words[0].lower() + ''.join(w.capitalize() for w in words[1:])
    elif case_type == "snake":
        return '_'.join(w.lower() for w in words)
    elif case_type == "kebab":
        return '-'.join(w.lower() for w in words)
        
    return text

def convert_unit(value: float, from_unit: str, to_unit: str):
    from_unit = from_unit.lower().strip()
    to_unit = to_unit.lower().strip()
    
    if from_unit == to_unit:
        return round(value, 4)
        
    length_factors = {
        'millimeter': 0.001, 'centimeter': 0.01, 'meter': 1.0, 'kilometer': 1000.0,
        'inch': 0.0254, 'foot': 0.3048, 'yard': 0.9144, 'mile': 1609.344, 'nautical_mile': 1852.0
    }
    
    weight_factors = {
        'milligram': 0.001, 'gram': 1.0, 'kilogram': 1000.0, 'metric_ton': 1000000.0,
        'ounce': 28.34952, 'pound': 453.59237, 'stone': 6350.29318
    }
    
    area_factors = {
        'square_meter': 1.0, 'square_kilometer': 1000000.0, 'hectare': 10000.0,
        'square_mile': 2589988.11, 'acre': 4046.85642, 'square_foot': 0.092903, 'square_inch': 0.00064516
    }
    
    volume_factors = {
        'milliliter': 0.001, 'liter': 1.0, 'cubic_meter': 1000.0,
        'gallon_us': 3.78541, 'quart_us': 0.946353, 'pint_us': 0.473176, 'cup_us': 0.24, 'fluid_ounce_us': 0.0295735,
        'cubic_foot': 28.3168, 'cubic_inch': 0.0163871
    }
    
    speed_factors = {
        'meter_per_second': 1.0, 'kilometer_per_hour': 0.277778, 'mile_per_hour': 0.44704, 'knot': 0.514444
    }
    
    time_factors = {
        'millisecond': 0.001, 'second': 1.0, 'minute': 60.0, 'hour': 3600.0,
        'day': 86400.0, 'week': 604800.0, 'month': 2628000.0, 'year': 31536000.0
    }
    
    data_factors = {
        'bit': 0.125, 'byte': 1.0, 'kilobyte': 1024.0, 'megabyte': 1048576.0,
        'gigabyte': 1073741824.0, 'terabyte': 1099511627776.0, 'petabyte': 1125899906842624.0
    }
    
    energy_factors = {
        'joule': 1.0, 'kilojoule': 1000.0, 'calorie': 4.184, 'kilocalorie': 4184.0, 'watt_hour': 3600.0, 'kilowatt_hour': 3600000.0, 'electron_volt': 1.60218e-19
    }
    
    pressure_factors = {
        'pascal': 1.0, 'kilopascal': 1000.0, 'bar': 100000.0, 'psi': 6894.76, 'atmosphere': 101325.0, 'torr': 133.322
    }
    
    if from_unit in ['celsius', 'fahrenheit', 'kelvin'] and to_unit in ['celsius', 'fahrenheit', 'kelvin']:
        # Convert to Celsius first
        c = value
        if from_unit == 'fahrenheit': c = (value - 32) * 5/9
        elif from_unit == 'kelvin': c = value - 273.15
            
        # Convert from Celsius to target
        if to_unit == 'fahrenheit': res = (c * 9/5) + 32
        elif to_unit == 'kelvin': res = c + 273.15
        else: res = c
        return round(res, 4)
    
    conversion_categories = [
        length_factors, weight_factors, area_factors, volume_factors, 
        speed_factors, time_factors, data_factors, energy_factors, pressure_factors
    ]
    
    for category in conversion_categories:
        if from_unit in category and to_unit in category:
            base_val = value * category[from_unit]
            return round(base_val / category[to_unit], 6) # Increased precision for larger ranges
            
    raise ValueError(f"Cannot convert {from_unit} to {to_unit}. They might be incompatible categories or unsupported units.")

def convert_currency(amount: float, from_currency: str, to_currency: str):
    from_currency = from_currency.upper().strip()
    to_currency = to_currency.upper().strip()
    
    if from_currency == to_currency:
        return round(amount, 2)
        
    try:
        # Using a free, no-auth public API
        url = f"https://open.er-api.com/v6/latest/{from_currency}"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            rates = data.get("rates", {})
            if to_currency in rates:
                rate = rates[to_currency]
                return round(amount * rate, 2)
            else:
                raise ValueError(f"Target currency '{to_currency}' is not supported.")
        else:
            raise ValueError(f"Source currency '{from_currency}' is not supported.")
    except Exception as e:
        raise ValueError(f"Currency conversion failed: {str(e)}")
