from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from database import get_db, ActivityLog



class ActivityBase(BaseModel):
    category: str
    planned_start: datetime
    planned_end: datetime

class ActivityCreate(ActivityBase):
    pass

class ActivityResponse(ActivityBase):
    id: int
    user_id: int
    actual_start: Optional[datetime] = None
    actual_end: Optional[datetime] = None
    delay_seconds: int = 0
    is_completed: bool
    
    model_config = ConfigDict(from_attributes=True)

class ActivityUpdate(BaseModel):
    is_completed: bool = True
    actual_end: datetime = datetime.now()



router = APIRouter(
    prefix="/activity",
    tags=["Logs"])

@router.post("/start", response_model=ActivityResponse)
async def start_activity(activity: ActivityCreate, db: AsyncSession = Depends(get_db)):
    now = datetime.now()
    delay = int((now - activity.planned_start).total_seconds())
    
    db_activity = ActivityLog(
        **activity.model_dump(),
        actual_start=now,
        delay_seconds=delay,
        user_id=1,
        is_completed=False
    )
    
    db.add(db_activity)

    await db.commit()
    await db.refresh(db_activity)

    return db_activity
