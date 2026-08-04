from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database import get_db
from models.user import User
from schemas.auth import GoogleLoginRequest, AuthResponse, UserResponse, ProfileUpdateRequest
from google.oauth2 import id_token
from google.auth.transport import requests
import os
import jwt
from datetime import datetime, timedelta

router = APIRouter()

JWT_SECRET = os.getenv("JWT_SECRET", "super-secret-key-change-me")
JWT_ALGORITHM = "HS256"

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=7)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return encoded_jwt

@router.post("/google", response_model=AuthResponse)
def google_login(request: GoogleLoginRequest, db: Session = Depends(get_db)):
    client_id = os.getenv("GOOGLE_CLIENT_ID", "129091157986-92ogmcbg3aqpbr00n80oern2r90saps6.apps.googleusercontent.com")
    
    try:
        if client_id:
            # Verify the token with Google
            idinfo = id_token.verify_oauth2_token(request.id_token, requests.Request(), client_id)
        else:
            # For development without a Client ID, we can bypass verification
            # WARNING: Do not use this in production!
            # If no client ID is set, we just decode the JWT to get the email
            import json
            import base64
            parts = request.id_token.split('.')
            if len(parts) != 3:
                raise ValueError("Invalid ID token format.")
            payload = parts[1]
            padded = payload + '=' * (4 - len(payload) % 4)
            idinfo = json.loads(base64.b64decode(padded).decode('utf-8'))
            
        if 'email' not in idinfo:
            raise HTTPException(status_code=400, detail="No email found in token")
            
        email = idinfo['email']
        google_id = idinfo.get('sub', '')
        full_name = idinfo.get('name', '')
        profile_pic = idinfo.get('picture', '')

        # Find or create user
        user = db.query(User).filter(User.email == email).first()
        if not user:
            user = User(
                email=email,
                google_id=google_id,
                full_name=full_name,
                profile_pic=profile_pic
            )
            db.add(user)
            db.commit()
            db.refresh(user)
        else:
            # Update info if changed
            if google_id and user.google_id != google_id:
                user.google_id = google_id
            if full_name and user.full_name != full_name:
                user.full_name = full_name
            if profile_pic and user.profile_pic != profile_pic:
                user.profile_pic = profile_pic
            db.commit()

        # Generate JWT
        access_token = create_access_token(data={"sub": user.email, "id": user.id})

        return AuthResponse(
            access_token=access_token,
            token_type="bearer",
            user=UserResponse.from_orm(user)
        )

    except ValueError as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/mock", response_model=AuthResponse)
def mock_login(db: Session = Depends(get_db)):
    email = "test@example.com"
    user = db.query(User).filter(User.email == email).first()
    if not user:
        user = User(email=email, google_id="mock123", full_name="Test User", profile_pic="")
        db.add(user)
        db.commit()
        db.refresh(user)
    access_token = create_access_token(data={"sub": user.email, "id": user.id})
    return AuthResponse(access_token=access_token, token_type="bearer", user=UserResponse.from_orm(user))

from fastapi.security import OAuth2PasswordBearer
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/google")

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user_id: int = payload.get("id")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid authentication credentials")
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")
        
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@router.get("/profile", response_model=UserResponse)
def get_profile(
    current_user: User = Depends(get_current_user)
):
    return UserResponse.from_orm(current_user)

@router.put("/profile", response_model=UserResponse)
def update_profile(
    profile_data: ProfileUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    current_user.company_name = profile_data.company_name
    current_user.company_logo_url = profile_data.company_logo_url
    current_user.company_address = profile_data.company_address
    current_user.whatsapp_number = profile_data.whatsapp_number
    current_user.phone_number = profile_data.phone_number
    current_user.gst_number = profile_data.gst_number
    current_user.business_type = profile_data.business_type
    current_user.bank_name = profile_data.bank_name
    current_user.account_name = profile_data.account_name
    current_user.account_number = profile_data.account_number
    current_user.ifsc_code = profile_data.ifsc_code
    if profile_data.pricing_mode:
        current_user.pricing_mode = profile_data.pricing_mode
    
    db.commit()
    db.refresh(current_user)
    
    return UserResponse.from_orm(current_user)

from schemas.auth import DeleteAccountRequest
from models.account_deletion import AccountDeletionRequest

@router.post("/delete-account")
def request_account_deletion(
    request: DeleteAccountRequest,
    db: Session = Depends(get_db)
):
    deletion_request = AccountDeletionRequest(
        email=request.email,
        reason=request.reason
    )
    db.add(deletion_request)
    db.commit()
    
    return {"status": "success", "message": "Account deletion request received."}
