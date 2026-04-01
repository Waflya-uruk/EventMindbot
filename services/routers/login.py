from fastapi import APIRouter, Depends, HTTPException
from niquests import Session
from pydantic import BaseModel

from core.security import verify_password
from database import get_db, get_user_by_email

router = APIRouter(
    prefix="/login",
    tags=["Login"]
)

class LoginRequest(BaseModel):
    email: str
    password: str

class LoginResponse(BaseModel):
    success: bool
    user_id: int


@router.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest,  db: Session = Depends(get_db)):
    try:
            user = get_user_by_email(db, request.email)

            if not user or not verify_password(request.password, user.password_hash):
                raise HTTPException(
                    status_code=401, 
                    detail="Неверный email или пароль"
                )

            return {
                "success": True,
                "user_id": user.id
            }
    except Exception as e:
        return f"ОШИБКА: {type(e).__name__} - {str(e)}"
