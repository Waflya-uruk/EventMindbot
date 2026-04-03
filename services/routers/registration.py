from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from database import get_db, create_user, get_user_by_email
from core.security import hash_password
from core.parsers import is_yandex_email
from core.logs import logger

router = APIRouter(
    prefix="/registration",
    tags=["Registration"]
)


class RegistrationRequest(BaseModel):
    name: str
    email: str
    password: str


@router.post("/register")
async def register_user(request: RegistrationRequest, db: AsyncSession = Depends(get_db)):
    try:
        user = await get_user_by_email(db, request.email)
        if user:
            return {"success": False, "message": "Пользователь уже зарегестрирован"}
        
        if not is_yandex_email(request.email):
            return {"success": False, "message": "Неверный email"}
        
        password_hash = hash_password(request.password)
        new_user = await create_user(db, request.name, request.email, password_hash)
        
        db.refresh(new_user)
        return {"success": True, "user_id": new_user.id}
    except Exception as e:
        logger.exception(e)
        return {"success": False}
    