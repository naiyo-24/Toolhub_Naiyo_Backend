from pydantic import BaseModel, Field
from typing import Optional, List

class FuelCostRequest(BaseModel):
    distance: float = Field(..., description="Distance to travel (in km or miles)")
    efficiency: float = Field(..., description="Fuel efficiency (e.g. 15 km/l or 30 mpg)")
    fuel_price: float = Field(..., description="Price per unit of fuel")

class WorldClockRequest(BaseModel):
    timezones: List[str] = Field(..., description="List of timezone names (e.g., ['America/New_York', 'Asia/Tokyo'])")

class CurrencyConverterRequest(BaseModel):
    amount: float = Field(..., description="Amount to convert")
    from_currency: str = Field(..., description="Base currency code (e.g. USD)")
    to_currency: str = Field(..., description="Target currency code (e.g. EUR)")

class WeatherRequest(BaseModel):
    location: str = Field(..., description="Name of the location to get weather for")

class TranslatorRequest(BaseModel):
    text: str = Field(..., description="Text to translate")
    target_language: str = Field(..., description="Language to translate into")
    source_language: Optional[str] = Field(None, description="Source language (optional, will auto-detect if omitted)")

class DistanceCalcRequest(BaseModel):
    origin: str = Field(..., description="Starting city/location")
    destination: str = Field(..., description="Destination city/location")

class TripPlannerRequest(BaseModel):
    destination: str = Field(..., description="Where are you going?")
    days: int = Field(..., description="Number of days")
    travel_style: str = Field("Balanced", description="E.g., Budget, Luxury, Backpacking, Family")

class PackingListRequest(BaseModel):
    destination: str = Field(..., description="Where are you going?")
    days: int = Field(..., description="Number of days")
    weather: str = Field("Variable", description="Expected weather (e.g. Hot, Cold, Rainy)")
