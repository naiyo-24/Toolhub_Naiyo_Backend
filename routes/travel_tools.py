from fastapi import APIRouter, HTTPException
import json
import urllib.request
import urllib.parse
from datetime import datetime
from zoneinfo import ZoneInfo
from schemas.travel_tools import (
    FuelCostRequest, WorldClockRequest, CurrencyConverterRequest,
    WeatherRequest, TranslatorRequest, DistanceCalcRequest,
    TripPlannerRequest, PackingListRequest
)
from routes.ai_tools import generate_ai_response

router = APIRouter()

# --- Math & Logic ---

@router.post("/fuel-cost-calc")
def fuel_cost_calc(req: FuelCostRequest):
    if req.efficiency <= 0:
        raise HTTPException(status_code=400, detail="Fuel efficiency must be greater than zero.")
    total_cost = (req.distance / req.efficiency) * req.fuel_price
    return {
        "distance": req.distance,
        "fuel_needed": round(req.distance / req.efficiency, 2),
        "total_cost": round(total_cost, 2)
    }

@router.post("/world-clock")
def world_clock(req: WorldClockRequest):
    results = {}
    for tz_str in req.timezones:
        try:
            tz = ZoneInfo(tz_str)
            now = datetime.now(tz)
            results[tz_str] = now.strftime("%Y-%m-%d %I:%M %p")
        except Exception:
            results[tz_str] = "Invalid Timezone"
    return {"times": results}

from zoneinfo import ZoneInfo, available_timezones

@router.get("/world-clock/timezones")
def get_timezones():
    # Return a sorted list of all valid timezones
    tzs = sorted(list(available_timezones()))
    return {"available_timezones": tzs}

# --- External APIs ---

@router.post("/currency-converter")
def currency_converter(req: CurrencyConverterRequest):
    try:
        url = f"https://api.exchangerate-api.com/v4/latest/{req.from_currency.upper()}"
        with urllib.request.urlopen(url) as response:
            data = json.loads(response.read().decode())
            
        rates = data.get("rates", {})
        to_curr = req.to_currency.upper()
        
        if to_curr not in rates:
            raise HTTPException(status_code=400, detail="Target currency not supported")
            
        converted = req.amount * rates[to_curr]
        return {
            "amount": req.amount,
            "from": req.from_currency.upper(),
            "to": to_curr,
            "converted_amount": round(converted, 2),
            "rate": rates[to_curr]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch exchange rates: {str(e)}")

@router.post("/weather")
def weather(req: WeatherRequest):
    try:
        # Use OpenStreetMap Nominatim to support hyper-local neighborhoods
        geo_url = f"https://nominatim.openstreetmap.org/search?q={urllib.parse.quote(req.location)}&format=json&limit=1"
        headers = {'User-Agent': 'ToolhubNaiyoApp/1.0'}
        req_obj = urllib.request.Request(geo_url, headers=headers)
        with urllib.request.urlopen(req_obj) as geo_res:
            geo_data = json.loads(geo_res.read().decode())
            
        if not geo_data:
            raise HTTPException(status_code=404, detail="Location not found. Try adding a city name.")
            
        lat = geo_data[0]["lat"]
        lon = geo_data[0]["lon"]
        
        # Simplify the display name
        display_name = geo_data[0].get("display_name", req.location)
        parts = display_name.split(",")
        resolved_name = f"{parts[0].strip()}"
        if len(parts) > 1:
            resolved_name += f", {parts[-1].strip()}"

        url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true"
        with urllib.request.urlopen(url) as response:
            data = json.loads(response.read().decode())
            
        current = data.get("current_weather", {})
        return {
            "Location": resolved_name,
            "Temperature": f"{current.get('temperature')} °C",
            "Windspeed": f"{current.get('windspeed')} km/h",
            "Time": "Day" if current.get("is_day") == 1 else "Night"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch weather: {str(e)}")

# --- AI Powered (Gemini) ---

@router.post("/translator")
def translator(req: TranslatorRequest):
    source = f" from {req.source_language}" if req.source_language else ""
    prompt = f"Translate the following text{source} into {req.target_language}. Return ONLY the translated text without quotes or markdown blocks: '{req.text}'"
    try:
        res = generate_ai_response(prompt)
        return {"translated_text": res.strip()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

import math

def haversine(lat1, lon1, lat2, lon2):
    R = 6371.0 # Earth radius in km
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

def geocode_location(location_name):
    geo_url = f"https://nominatim.openstreetmap.org/search?q={urllib.parse.quote(location_name)}&format=json&limit=1"
    headers = {'User-Agent': 'ToolhubNaiyoApp/1.0'}
    req_obj = urllib.request.Request(geo_url, headers=headers)
    with urllib.request.urlopen(req_obj) as geo_res:
        geo_data = json.loads(geo_res.read().decode())
    if not geo_data:
        raise HTTPException(status_code=404, detail=f"Location not found: {location_name}")
    return float(geo_data[0]["lat"]), float(geo_data[0]["lon"]), geo_data[0].get("display_name").split(",")[0]

@router.post("/distance-calc")
def distance_calc(req: DistanceCalcRequest):
    try:
        lat1, lon1, name1 = geocode_location(req.origin)
        lat2, lon2, name2 = geocode_location(req.destination)
        
        flight_distance = haversine(lat1, lon1, lat2, lon2)
        
        driving_distance = None
        try:
            osrm_url = f"http://router.project-osrm.org/route/v1/driving/{lon1},{lat1};{lon2},{lat2}?overview=false"
            req_obj = urllib.request.Request(osrm_url, headers={'User-Agent': 'ToolhubNaiyoApp/1.0'})
            with urllib.request.urlopen(req_obj) as osrm_res:
                osrm_data = json.loads(osrm_res.read().decode())
                if osrm_data.get("code") == "Ok":
                    # Distance is in meters, convert to km
                    driving_distance = osrm_data["routes"][0]["distance"] / 1000.0
        except Exception:
            pass # OSRM might fail or rate limit, fallback to just flight distance
            
        result = {
            "origin": name1,
            "destination": name2,
            "flight_distance_km": round(flight_distance, 1)
        }
        
        if driving_distance:
            result["driving_distance_km"] = round(driving_distance, 1)
            
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to calculate distance: {str(e)}")

@router.post("/trip-planner")
def trip_planner(req: TripPlannerRequest):
    prompt = f"Create a {req.days}-day {req.travel_style} travel itinerary for {req.destination}. Format the output as a JSON list of objects, where each object has 'day' (int) and 'activities' (list of strings)."
    try:
        res = generate_ai_response(prompt, json_mode=True)
        try:
            start = res.find('[')
            end = res.rfind(']') + 1
            if start != -1 and end != 0:
                itinerary = json.loads(res[start:end])
            else:
                itinerary = json.loads(res)
        except Exception:
            itinerary = [{"error": "Failed to parse", "raw": res}]
        return {"itinerary": itinerary}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/packing-list")
def packing_list(req: PackingListRequest):
    prompt = f"Generate a packing list for a {req.days}-day trip to {req.destination}. The expected weather is {req.weather}. Format the output as a JSON list of strings representing items to pack."
    try:
        res = generate_ai_response(prompt, json_mode=True)
        try:
            start = res.find('[')
            end = res.rfind(']') + 1
            if start != -1 and end != 0:
                items = json.loads(res[start:end])
            else:
                items = json.loads(res)
        except Exception:
            items = ["Failed to parse list", res]
        return {"packing_list": items}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
