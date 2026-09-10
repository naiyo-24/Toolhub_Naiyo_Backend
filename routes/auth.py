from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database import get_db
from models.user import User, Session as AppSession
from schemas.auth import GoogleLoginRequest, AuthResponse, UserResponse, ProfileUpdateRequest, RefreshRequest, TokenResponse
from core.security import create_access_token, create_refresh_token, get_password_hash, verify_password
from google.auth.transport import requests
from google.oauth2 import id_token
import os
import jwt
from datetime import datetime, timedelta

router = APIRouter()

@router.post("/google", response_model=AuthResponse)
@router.post("/login/google", response_model=AuthResponse)
def google_login(request: GoogleLoginRequest, db: Session = Depends(get_db)):
    client_id = os.getenv("GOOGLE_CLIENT_ID", "129091157986-92ogmcbg3aqpbr00n80oern2r90saps6.apps.googleusercontent.com")
    
    actual_token = request.id_token or request.token
    if not actual_token:
        raise HTTPException(status_code=422, detail="Missing id_token or token in request body")
        
    try:
        if client_id:
            # Verify the token with Google
            idinfo = id_token.verify_oauth2_token(actual_token, requests.Request(), client_id)
        else:
            # For development without a Client ID, we can bypass verification
            # WARNING: Do not use this in production!
            # If no client ID is set, we just decode the JWT to get the email
            import json
            import base64
            parts = actual_token.split('.')
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
        access_token = create_access_token(subject=user.id)
        refresh_token = create_refresh_token(subject=user.id)
        
        # passlib's bcrypt is fundamentally broken with long strings in this version.
        # We will use plain SHA-256 to hash the refresh token in the DB.
        import hashlib
        refresh_token_hash = hashlib.sha256(refresh_token.encode()).hexdigest()

        # Store session
        user_session = AppSession(
            user_id=user.id,
            refresh_token_hash=refresh_token_hash,
            device_name="Flutter App"
        )
        db.add(user_session)
        db.commit()

        return AuthResponse(
            access_token=access_token,
            token_type="bearer",
            user=UserResponse.model_validate(user),
            refresh_token=refresh_token
        )

    except ValueError as e:
        with open("token_error.log", "w") as f:
            f.write(f"Google Token Error: {str(e)}")
        raise HTTPException(status_code=401, detail=f"Invalid token: {str(e)}")
    except Exception as e:
        import traceback
        with open("error.log", "w") as f:
            f.write(traceback.format_exc())
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
    access_token = create_access_token(subject=user.id)
    return AuthResponse(access_token=access_token, token_type="bearer", user=UserResponse.model_validate(user))

@router.post("/refresh", response_model=TokenResponse)
def refresh_token(request: RefreshRequest, db: Session = Depends(get_db)):
    from jose import jwt, JWTError
    from core.security import SECRET_KEY, ALGORITHM
    try:
        payload = jwt.decode(request.refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = int(payload.get("sub"))
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    # verify in db
    user_sessions = db.query(AppSession).filter(AppSession.user_id == user_id, AppSession.revoked_at == None).all()
    valid_session = None
    for s in user_sessions:
        import hashlib
        token_hash = hashlib.sha256(request.refresh_token.encode()).hexdigest()
        if token_hash == s.refresh_token_hash:
            valid_session = s
            break
            
    if not valid_session:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    access_token = create_access_token(subject=user_id)
    return TokenResponse(access_token=access_token)

from fastapi.security import OAuth2PasswordBearer
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/google")

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    from core.security import SECRET_KEY, ALGORITHM
    from jose import jwt, JWTError
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id_str = payload.get("sub")
        if user_id_str is None:
            raise HTTPException(status_code=401, detail="Invalid authentication credentials")
        user_id = int(user_id_str)
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")
        
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@router.get("/profile", response_model=UserResponse)
def get_profile(
    current_user: User = Depends(get_current_user)
):
    return UserResponse.model_validate(current_user)

@router.put("/profile", response_model=UserResponse)
@router.post("/profile", response_model=UserResponse)
def update_profile(
    profile_data: ProfileUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    update_data = profile_data.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(current_user, key, value)
    
    db.commit()
    db.refresh(current_user)
    
    return UserResponse.model_validate(current_user)

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

@router.post("/logout")
def logout(current_user: User = Depends(get_current_user)):
    # Since JWTs are stateless, we simply acknowledge the request here.
    # The actual logout happens by clearing the token on the frontend.
    # In the future, this can be used to add the token to a blacklist.
    return {"status": "success", "message": "Successfully logged out"}

