import datetime
from sqlalchemy import and_, desc, select

from database.database import User, UserEvent, CalendarAccount, Author, AuthorEvent, get_db
from sqlalchemy.orm import Session, joinedload



def create_user(db: Session, name:str, email: str, password_hash: str):
    new_user = User(name=name, email=email, password_hash=password_hash)
    db.add(new_user)
    db.commit()
    return new_user

def get_user_by_id(db: Session, id: int):
    query = select(User).where(User.id == id)
    return db.execute(query).scalar_one_or_none()
    
def get_user_by_email(db: Session, email: str):
    query = select(User).where(User.email == email)
    return db.execute(query).scalar_one_or_none()


def create_yandex_calendar(db: Session, user_id: int, email: str, refresh_token: str):
    new_calendar = CalendarAccount(user_id=user_id, email=email, provider="yandex", refresh_token=refresh_token)
    db.add(new_calendar)
    db.commit()

def get_yandex_account(db: Session, user_id: int):
    query = select(CalendarAccount).where(
        CalendarAccount.user_id == user_id,
        CalendarAccount.provider == "yandex"
    )
    return db.execute(query).scalar_one_or_none()

def create_google_calendar(db: Session, user_id: int, email: str, refresh_token: str):
    new_calendar = CalendarAccount(user_id=user_id, email=email, provider="google", refresh_token=refresh_token)
    db.add(new_calendar)
    db.commit()

def get_google_account(db: Session, user_id: int):
    query = select(CalendarAccount).where(
        CalendarAccount.user_id == user_id,
        CalendarAccount.provider == "google"
    )
    return db.execute(query).scalar_one_or_none()

def get_user_calendars(db: Session, user_id: int):
    query = select(CalendarAccount).where(CalendarAccount.user_id == user_id)
    return db.execute(query).scalars().all()


def create_event(db: Session, user_id: int, title: str, description: str, start_time: str, end_time:str):
    new_user = UserEvent(user_id=user_id, title=title, description=description, start_time = start_time, end_time=end_time)
    db.add(new_user)
    db.commit()

def get_user_events(db: Session, user_id: int, limit: int = 10):
    query = (
        select(UserEvent)
        .where(UserEvent.user_id == user_id)
        .order_by(UserEvent.start_time.asc())
        .limit(limit)
    )
    return db.execute(query).scalars().all()

def get_event_by_id(db: Session, event_id: int):
    return db.get(UserEvent, event_id)



def get_recommendations(db: Session, now_date:str, min_rating=4.0, categories=None):
    """
    Формирует ленту рекомендованных событий на основе рейтинга автора и категорий.
    """
    now_date = datetime.fromisoformat(now_date)
    
    query = (
        select(AuthorEvent)
        .join(AuthorEvent.author)
        .options(joinedload(AuthorEvent.author))
        .where(
            and_(
                AuthorEvent.is_active == True,
                Author.rating >= min_rating,
                (AuthorEvent.start_time >= now_date) | (AuthorEvent.start_time == None)
            )
        )
    )

    if categories:
        query = query.where(AuthorEvent.category.in_(categories))

    query = query.order_by(
        desc(Author.rating), 
        desc(AuthorEvent.created_at)
    )
    
    result = db.execute(query)
    return result.scalars().all()
