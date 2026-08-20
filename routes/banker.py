from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database import get_db
from models.user import User
from models.banker_profile import BankerProfile
from schemas.banker import BankerProfileResponse, BankerProfileUpdate
from routes.auth import get_current_user

router = APIRouter()

@router.get("/profile", response_model=BankerProfileResponse)
def get_banker_profile(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    profile = db.query(BankerProfile).filter(BankerProfile.user_id == current_user.id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Banker profile not found")
    return profile

@router.post("/profile", response_model=BankerProfileResponse)
def create_banker_profile(profile_data: BankerProfileUpdate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    profile = db.query(BankerProfile).filter(BankerProfile.user_id == current_user.id).first()
    if profile:
        raise HTTPException(status_code=400, detail="Banker profile already exists")
    
    profile = BankerProfile(
        user_id=current_user.id,
        mobile=profile_data.mobile,
        role=profile_data.role,
        designation=profile_data.designation,
        employee_id=profile_data.employee_id,
        experience_years=profile_data.experience_years,
        org_type=profile_data.org_type,
        org_name=profile_data.org_name,
        branch_name=profile_data.branch_name,
        city=profile_data.city,
        state_region=profile_data.state_region,
        loan_types=profile_data.loan_types
    )
    db.add(profile)
    db.commit()
    db.refresh(profile)
    return profile

@router.patch("/profile", response_model=BankerProfileResponse)
def update_banker_profile(profile_data: BankerProfileUpdate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    profile = db.query(BankerProfile).filter(BankerProfile.user_id == current_user.id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Banker profile not found")
    
    if profile_data.mobile is not None:
        profile.mobile = profile_data.mobile
    if profile_data.role is not None:
        profile.role = profile_data.role
    if profile_data.designation is not None:
        profile.designation = profile_data.designation
    if profile_data.employee_id is not None:
        profile.employee_id = profile_data.employee_id
    if profile_data.experience_years is not None:
        profile.experience_years = profile_data.experience_years
    if profile_data.org_type is not None:
        profile.org_type = profile_data.org_type
    if profile_data.org_name is not None:
        profile.org_name = profile_data.org_name
    if profile_data.branch_name is not None:
        profile.branch_name = profile_data.branch_name
    if profile_data.city is not None:
        profile.city = profile_data.city
    if profile_data.state_region is not None:
        profile.state_region = profile_data.state_region
    if profile_data.loan_types is not None:
        profile.loan_types = profile_data.loan_types

    db.commit()
    db.refresh(profile)
    return profile
