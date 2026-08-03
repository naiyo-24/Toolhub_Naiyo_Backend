from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import firebase_admin
from firebase_admin import credentials, auth

# Initialize Firebase (this assumes a service account key will be provided)
# In production, this should be wrapped in an app startup event or try/except
try:
    cred = credentials.ApplicationDefault() # Or credentials.Certificate("path/to/key.json")
    firebase_admin.initialize_app(cred)
except ValueError:
    pass # App already initialized or no credentials found

security = HTTPBearer()

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    try:
        decoded_token = auth.verify_id_token(token)
        return decoded_token
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
