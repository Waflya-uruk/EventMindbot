from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
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


@router.post("/", response_model=LoginResponse)
async def login(request: LoginRequest,  db: AsyncSession = Depends(get_db)):
    try:
            user = await get_user_by_email(db, request.email)

            if not user or not verify_password(request.password, user.password_hash):
                return {
                    "success": False,
                    "user_id": -1
                }

            return {
                "success": True,
                "user_id": user.id
            }
    except Exception as e:
        return {
            "success": False,
            "user_id": -1
        }
