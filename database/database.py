import os
import datetime
from typing import List, Optional
from sqlalchemy import ForeignKey, String, Text, DateTime, Boolean, Float, types, inspect, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, sessionmaker, mapped_column, relationship
from core.security import encrypt_data, decrypt_data, hash_password


class Base(DeclarativeBase):
    pass


# КАСТОМНЫЕ ТИПЫ ДАННЫХ
class EncryptedString(types.TypeDecorator):
    impl = types.Text
    cache_ok = True
    def process_bind_param(self, value, dialect):
        return encrypt_data(value) if value else None
    def process_result_value(self, value, dialect):
        return decrypt_data(value) if value else None

class HashedString(types.TypeDecorator):
    impl = types.String
    cache_ok = True
    def process_bind_param(self, value, dialect):
        return hash_password(value) if value else None


# МОДЕЛИ ПОЛЬЗОВАТЕЛЕЙ
class User(Base):
    __tablename__ = 'users'
    
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    password_hash: Mapped[Optional[str]] = mapped_column(HashedString, nullable=False)
    
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
    start_time: Mapped[datetime.datetime] = mapped_column(DateTime, nullable=False)
    end_time: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime)
    sync_status: Mapped[str] = mapped_column(String(50), default="pending")
    yandex_uid: Mapped[str | None] = mapped_column(unique=True, nullable=True)
    
    user: Mapped["User"] = relationship(back_populates="events")


# МОДЕЛИ СЕРВЕРА
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
    start_time: Mapped[datetime.datetime] = mapped_column(DateTime)
    end_time: Mapped[datetime.datetime] = mapped_column(DateTime)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, default=datetime.datetime.now(datetime.timezone.utc)
    )
    
    author: Mapped["Author"] = relationship(back_populates="author_events")


# КОНФИГУРАЦИЯ И СЕССИЯ
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://odoo:odoo@db:5432/postgres")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    Base.metadata.create_all(bind=engine)
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    print(f"Сейчас в базе есть таблицы: {tables}")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()