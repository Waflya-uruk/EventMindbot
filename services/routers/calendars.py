from typing import List
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from core.parsers import is_yandex_email
from core.logs import logger
from database import (
    CalendarAccount,
    get_db,
    create_calendar, delete_calendar_by_email
)

router = APIRouter(
    prefix="/calendars",
    tags=["Calendars"]
)

class CalendarRequest(BaseModel):
    user_id: int
    email: str
    app_password: str

class CalendarResponse(BaseModel):
    success: bool
    message: str

class CalendarAccountResponse(BaseModel):
    email: str
    app_password: str

    class Config:
        from_attributes = True

@router.post("/save", response_model=CalendarResponse)
async def calendar_save(request: CalendarRequest, db: AsyncSession = Depends(get_db)):
    if not is_yandex_email(request.email):
        return {"success": False, "message": "Неверный email"}


    query = select(CalendarAccount).where(CalendarAccount.email == request.email)
    result = await db.execute(query)
    existing_account = result.scalar_one_or_none()

    if existing_account:
        return {"success": False, "message": f"ОШИБКА: Календарь {request.email} уже зарегистрирован"}

    await create_calendar(db, request.user_id, request.email, request.app_password)
    return {"success": True, "message": "Календарь успешно создан"}

@router.post("/delete", response_model=CalendarResponse)
async def calendar_delete(request: CalendarRequest, db: AsyncSession = Depends(get_db)):
    success = await delete_calendar_by_email(db, request.email)
    result = "Аккаунт успешно удален" if success else "Ошибка: Аккаунт не найден"
    return {"success": success, "message": result}

@router.get("/get", response_model=List[CalendarAccountResponse])
async def get_calendars(user_id: int = Query(), db: AsyncSession = Depends(get_db)):
    query = select(CalendarAccount).where(CalendarAccount.user_id == user_id)
    result = await db.execute(query)
    accounts = result.scalars().all()
    return accounts