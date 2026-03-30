from typing import List

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from database.service import (
    create_calendar, delete_calendar_by_email
)
from database.database import (
    CalendarAccount,
    get_db
)

router = APIRouter(
    prefix="/calendars",
    tags=["Calendars"]
)

class CalendarRequest(BaseModel):
    user_id: int
    email: str
    password_token: str
    save: bool

class CalendarResponse(BaseModel):
    success: bool
    message: str

class CalendarAccountResponse(BaseModel):
    email: str
    password_token: str

    class Config:
        from_attributes = True

@router.post("/save", response_model=CalendarResponse)
async def calendar_save(request: CalendarRequest, db: AsyncSession = Depends(get_db)):
    success = False
    result = "Неизвестная ОШИБКА"

    try:
        query = select(CalendarAccount).where(CalendarAccount.email == request.email)
        result = await db.execute(query)
        existing_account = result.scalar_one_or_none()

        if not existing_account:
            try:
                create_calendar(db, request.user_id, request.email, request.password_token)
                success = True
                result = "Календарь успешно создан и привязан"
            except Exception as e:
                db.rollback()
                result = f"ОШИБКА при создании календаря: {str(e)}"
        else:
            success = False
            result = f"ОШИБКА: Календарь {request.email} уже зарегистрирован"
        return {"success": success, "message": result}
    except Exception as e:
        return f"ОШИБКА: {type(e).__name__} - {str(e)}"
    
@router.post("/delete", response_model=CalendarResponse)
async def calendar_save(request: CalendarRequest, db: AsyncSession = Depends(get_db)):
    success = False
    result = "Неизвестная ОШИБКА"

    try:
        success = delete_calendar_by_email(db, request.email)
        result = "Аккаунт успешно удален" if success else "Ошибка: Аккаунт не найден"
        return {"success": success, "message": result}
    except Exception as e:
        return f"ОШИБКА: {type(e).__name__} - {str(e)}"

@router.get("/", response_model=List[CalendarAccountResponse])
async def get_calendars(user_id: int = Query(), db: AsyncSession = Depends(get_db)):
    try:
        query = select(CalendarAccount).where(CalendarAccount.user_id == user_id)
        result = await db.execute(query)
        accounts = result.scalars().all()
        return accounts
    except Exception as e:
        return f"ОШИБКА: {type(e).__name__} - {str(e)}"