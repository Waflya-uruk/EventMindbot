from fastapi import APIRouter, Depends
from niquests import Session
from pydantic import BaseModel

from database.database import get_db
from database.service import create_user, get_user_by_email
from core.security import hash_password

router = APIRouter(
    prefix="/registration",
    tags=["Registration"]
)


class RegistrationRequest(BaseModel):
    name: str
    email: str
    password: str


@router.post("/register")
async def register_user(request: RegistrationRequest, db: Session = Depends(get_db)):
    try:
        user=get_user_by_email(db, request.email)
        
        if user:
            return {"success": False, "message": "Пользователь уже зарегестрирован"}
        password_hash = hash_password(request.password)
        new_user = create_user(db, request.name, request.email, password_hash)
        
        db.refresh(new_user)
        return {"success": True, "user_id": new_user.id}
    except Exception as e:
        return f"ОШИБКА: {type(e).__name__} - {str(e)}"