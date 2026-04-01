from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from sqlalchemy import delete, select
from .models import User, UserEvent, CalendarAccount, Author, AuthorEvent



# USER
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


# CALENDAR ACCOUNT
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
        await db.commit()
        return True
    return False


# USER EVENT
async def create_event(db: AsyncSession, user_id: int, title: str, description: str, start_time: str, end_time:str):
    new_event = UserEvent(user_id=user_id, title=title, description=description, start_time = start_time, end_time=end_time)
    db.add(new_event)
    await db.commit()
    await db.refresh(new_event)
    return new_event

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


# AUTHOR
async def create_author(db: AsyncSession, nickname: str, rating: float = 5.0) -> Author:
    new_author = Author(nickname=nickname, rating=rating)
    db.add(new_author)
    await db.commit()
    await db.refresh(new_author)
    return new_author

async def get_author_by_id(db: AsyncSession, author_id: int, include_events: bool = False) -> Optional[Author]:
    query = select(Author).where(Author.id == author_id)
    
    if include_events:
        query = query.options(joinedload(Author.author_events))
        
    result = await db.execute(query)
    return result.unique().scalar_one_or_none()

async def get_all_authors(db: AsyncSession) -> List[Author]:
    query = select(Author).order_by(Author.rating.desc())
    result = await db.execute(query)
    return result.scalars().all()

async def delete_author(db: AsyncSession, author_id: int) -> bool:
    query = delete(Author).where(Author.id == author_id)
    result = await db.execute(query)
    await db.commit()
    
    return result.rowcount > 0


# AUTHOR EVENT
async def create_author_event(db: AsyncSession, event_data: dict) -> AuthorEvent:
    new_event = AuthorEvent(**event_data)
    db.add(new_event)
    await db.commit()
    await db.refresh(new_event)
    return new_event

async def get_author_events(db: AsyncSession, author_id: Optional[int] = None, active_only: bool = True) -> List[AuthorEvent]:
    query = select(AuthorEvent)
    
    if author_id:
        query = query.where(AuthorEvent.author_id == author_id)
    if active_only:
        query = query.where(AuthorEvent.is_active == True)
        
    query = query.order_by(AuthorEvent.start_time.asc())
    
    result = await db.execute(query)
    return result.scalars().all()

async def get_event_by_id(db: AsyncSession, event_id: int) -> Optional[AuthorEvent]:
    result = await db.execute(select(AuthorEvent).where(AuthorEvent.id == event_id))
    return result.scalar_one_or_none()

async def delete_author_event(db: AsyncSession, event_id: int) -> bool:
    query = delete(AuthorEvent).where(AuthorEvent.id == event_id)
    result = await db.execute(query)
    await db.commit()
    
    return result.rowcount > 0
