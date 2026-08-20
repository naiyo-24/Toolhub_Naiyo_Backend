from database import SessionLocal
from models.user import User
from core.security import create_access_token

db = SessionLocal()
user = db.query(User).filter_by(id=2).first()
if user:
    token = create_access_token(subject=user.id)
    print(token)
