import datetime
import os
from dataclasses import dataclass
from typing import List, Optional
from sqlalchemy import (
    ForeignKey, String, Text, DateTime, Boolean, Float, types,
    inspect, create_engine
)
from sqlalchemy.orm import (
    DeclarativeBase, Mapped,
    mapped_column, relationship
)
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from core.security import encrypt_data, decrypt_data

@dataclass
class Settings:
    POSTGRES_USER: str = os.getenv("POSTGRES_USER", "postgres")
    POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD", "")
    POSTGRES_DB: str = os.getenv("POSTGRES_DB", "postgres")
    POSTGRES_HOST: str = os.getenv("POSTGRES_HOST", "db")
    POSTGRES_PORT: str = os.getenv("POSTGRES_PORT", "5432")

    @property
    def DATABASE_URL(self) -> str:
        return (
            f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

settings = Settings()


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

DATABASE_URL = settings.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")

engine = create_async_engine(DATABASE_URL, echo=True)
AsyncSessionLocal = async_sessionmaker(
    bind=engine, 
    class_=AsyncSession, 
    expire_on_commit=False
)

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        
        def get_tables(connection):
            return inspect(connection).get_table_names()
        
        tables = await conn.run_sync(get_tables)
        print(f"🚀 База готова. Таблицы: {tables}")

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session