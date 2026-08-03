from fastapi import APIRouter, Request
import datetime

router = APIRouter()

@router.post("/bmi-calculator")
async def bmi_calculator(request: Request):
    data = await request.json()
    weight = float(data.get("weight", 0))
    height = float(data.get("height", 0)) / 100.0  # assuming cm
    
    if height > 0:
        bmi = weight / (height * height)
    else:
        bmi = 0
        
    category = "Normal"
    if bmi < 18.5:
        category = "Underweight"
    elif bmi >= 25 and bmi < 30:
        category = "Overweight"
    elif bmi >= 30:
        category = "Obese"
        
    return {
        "BMI": f"{bmi:.1f}",
        "Category": category
    }

@router.post("/medicine-alert")
async def medicine_alert(request: Request):
    data = await request.json()
    return {
        "Message": f"Alert set for {data.get('medication_name')} at {data.get('time_to_take')}."
    }

@router.post("/water-tracker")
async def water_tracker(request: Request):
    data = await request.json()
    amount = data.get('amount_ml', 0)
    reminder_type = data.get('reminder_type', 'Not specified')
    return {
        "Message": f"Water Reminder set for {amount}ml ({reminder_type})."
    }

@router.post("/calorie-calculator")
async def calorie_calculator(request: Request):
    data = await request.json()
    return {
        "Message": f"Logged {data.get('calories', 0)} calories for {data.get('meal_name')}."
    }

@router.post("/step-counter")
async def step_counter(request: Request):
    data = await request.json()
    return {
        "Message": f"Logged {data.get('steps', 0)} steps today."
    }

@router.post("/sleep-tracker")
async def sleep_tracker(request: Request):
    data = await request.json()
    return {
        "Message": f"Logged {data.get('hours_slept', 0)} hours of sleep. Quality: {data.get('quality')}."
    }

@router.post("/period-tracker")
async def period_tracker(request: Request):
    data = await request.json()
    return {
        "Message": f"Logged period starting {data.get('start_date')}."
    }

@router.post("/habit-tracker")
async def habit_tracker(request: Request):
    data = await request.json()
    return {
        "Message": f"Logged habit: {data.get('habit_name')}."
    }
