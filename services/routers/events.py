from datetime import datetime
from typing import List
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from core.logs import logger
from database import (
    UserEvent,
    get_db
)

from core.ai import *

router = APIRouter(
    prefix="/events",
    tags=["Event"]
)

class EventsResponse(BaseModel):
    id: int
    start_time: datetime
    title: str
    
    class Config:
        from_attributes = True


@router.get("/", response_model=List[EventsResponse])
async def get_events(user_id: int = Query(), db: AsyncSession = Depends(get_db)):
    query = select(UserEvent).where(UserEvent.user_id == user_id)
    result = await db.execute(query)
    accounts = result.scalars().all()
    return accounts