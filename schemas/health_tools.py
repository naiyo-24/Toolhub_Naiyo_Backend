from pydantic import BaseModel, Field
from typing import Optional
import datetime

class BMICalculatorRequest(BaseModel):
    weight_kg: float = Field(..., description="Weight in Kilograms")
    height_cm: float = Field(..., description="Height in Centimeters")

class WaterTrackerRequest(BaseModel):
    amount_ml: int = Field(..., description="Amount of water consumed in ml")

class MedicineAlertRequest(BaseModel):
    medication_name: str = Field(..., description="Name of the medicine")
    dosage: str = Field(..., description="Dosage (e.g. 1 pill, 500mg)")
    time_to_take: datetime.time = Field(..., description="Time to take the medicine (HH:MM:SS)")

class CalorieCalcRequest(BaseModel):
    meal_name: str = Field(..., description="Name of the meal")
    calories: int = Field(..., description="Calories consumed")

class StepCounterRequest(BaseModel):
    steps: int = Field(..., description="Number of steps taken today")

class SleepTrackerRequest(BaseModel):
    hours_slept: float = Field(..., description="Number of hours slept")
    quality: str = Field(..., description="Quality of sleep (e.g., Good, Fair, Poor)")

class PeriodTrackerRequest(BaseModel):
    start_date: datetime.date = Field(..., description="Start date of the cycle (YYYY-MM-DD)")
    end_date: Optional[datetime.date] = Field(None, description="End date of the cycle (YYYY-MM-DD)")
    symptoms: Optional[str] = Field(None, description="Any symptoms experienced")

class HabitTrackerRequest(BaseModel):
    habit_name: str = Field(..., description="Name of the habit (e.g., Reading, Gym)")
