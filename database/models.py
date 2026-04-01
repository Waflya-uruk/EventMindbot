from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy import (
    Column, ForeignKey,
    Integer, String, Text, DateTime, Boolean, Float,
    func, types
)
from sqlalchemy.orm import (
    DeclarativeBase, Mapped,
    mapped_column, relationship
)
from core.security import encrypt_data, decrypt_data



class Base(DeclarativeBase):
    pass



# КАСТОМНЫЙ ТИПЫ ДАННЫХ
class EncryptedString(types.TypeDecorator):
    impl = types.Text
    cache_ok = True
    def process_bind_param(self, value, dialect):
        return encrypt_data(value) if value else None
    def process_result_value(self, value, dialect):
        return decrypt_data(value) if value else None



# МОДЕЛИ ПОЛЬЗОВАТЕЛЕЙ
class User(Base):
    __tablename__ = 'users'
    
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    password_hash: Mapped[Optional[str]] = mapped_column(String, nullable=False)
    
    calendar_accounts: Mapped[List["CalendarAccount"]] = relationship(back_populates="user")
    events: Mapped[List["UserEvent"]] = relationship(back_populates="user")

class CalendarAccount(Base):
    __tablename__ = 'calendar_accounts'
    
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'))
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    app_password: Mapped[Optional[str]] = mapped_column(EncryptedString, nullable=False)
    
    user: Mapped["User"] = relationship(back_populates="calendar_accounts")

class UserEvent(Base):
    __tablename__ = 'user_events'
    
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'))

    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[Optional[str]] = mapped_column(Text)

    start_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    end_time: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    
    sync_status: Mapped[str] = mapped_column(String(50), default="pending")
    
    user: Mapped["User"] = relationship(back_populates="events")



# МОДЕЛИ АВТОРОВ
class Author(Base):
    __tablename__ = 'authors'
    
    id: Mapped[int] = mapped_column(primary_key=True)
    nickname: Mapped[str] = mapped_column(String(100), unique=True)
    rating: Mapped[float] = mapped_column(Float, default=5.0)
    
    author_events: Mapped[List["AuthorEvent"]] = relationship(back_populates="author")

class AuthorEvent(Base):
    __tablename__ = 'author_events'
    
    id: Mapped[int] = mapped_column(primary_key=True)
    author_id: Mapped[int] = mapped_column(ForeignKey('authors.id'))
    user_id: Mapped[Optional[int]] = mapped_column(ForeignKey('users.id'))

    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[Optional[str]] = mapped_column(Text)
    category: Mapped[Optional[str]] = mapped_column(String(100))

    start_time: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    end_time: Mapped[datetime] = mapped_column(DateTime(timezone=True))

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now()
    )
    
    author: Mapped["Author"] = relationship(back_populates="author_events")



# МОДЕЛИ НЕЙРОСЕТИ
class ActivityLog(Base):
    __tablename__ = "activity_logs"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(index=True)
    category: Mapped[str] = mapped_column(String(100)) # 'Work', 'Sport', 'Education'

    # Первоначальный план
    original_planned_start: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    
    # Текущий план (после всех переносов)
    final_planned_start: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    
    # Сколько раз пользователь попросил бота подвинуть время
    reschedule_count: Mapped[int] = mapped_column(default=0)
    
    is_completed: Mapped[bool] = mapped_column(default=False)
    
    # Разница в секундах между самым первым планом и итоговым временем
    total_shift_seconds: Mapped[int] = mapped_column(default=0)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now()
    )
