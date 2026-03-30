from sqlalchemy import and_, desc, select

from database.database import User, UserEvent, CalendarAccount, Author, AuthorEvent
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload



async def create_user(db: AsyncSession, name:str, email: str, password_hash: str):
    new_user = User(name=name, email=email, password_hash=password_hash)
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    return new_user

async def get_user_by_id(db: AsyncSession, id: int):
    query = select(User).where(User.id == id)
    result = await db.execute(query)
    user = result.scalar_one_or_none()
    return user
    
async def get_user_by_email(db: AsyncSession, email: str):
    query = select(User).where(User.email == email)
    result = await db.execute(query)
    return result.scalar_one_or_none()


async def create_calendar(db: AsyncSession, user_id: int, email: str, app_password: str):
    new_calendar = CalendarAccount(user_id=user_id, email=email, app_password=app_password)
    db.add(new_calendar)
    await db.commit()
    await db.refresh(new_calendar)
    return new_calendar

async def get_calendar_by_id(db: AsyncSession, user_id: int):
    query = select(CalendarAccount).where(CalendarAccount.user_id == user_id)
    result = await db.execute(query)
    account = result.scalar_one_or_none()
    return account

async def get_calendars_by_id(db: AsyncSession, user_id: int):
    query = select(CalendarAccount).where(CalendarAccount.user_id == user_id)
    result = await db.execute(query)
    calendars = result.scalars().all()
    return calendars

async def delete_calendar_by_email(db: AsyncSession, email: str) -> bool:
    query = select(CalendarAccount).filter(CalendarAccount.email == email)
    result = await db.execute(query)
    account = result.scalars().first()
    if account:
        db.delete(account)
        db.commit()
        return True
    return False


async def create_event(db: AsyncSession, user_id: int, title: str, description: str, start_time: str, end_time:str):
    new_user = UserEvent(user_id=user_id, title=title, description=description, start_time = start_time, end_time=end_time)
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    return new_user

async def get_user_events(db: AsyncSession, user_id: int, limit: int = 10):
    query = (
        select(UserEvent)
        .where(UserEvent.user_id == user_id)
        .order_by(UserEvent.start_time.asc())
        .limit(limit)
    )
    result = await db.execute(query)
    events = result.scalars().all()
    return events
