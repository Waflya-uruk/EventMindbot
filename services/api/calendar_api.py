import calendar
from caldav import aio
from datetime import datetime
from sqlalchemy import select

from core.logs import logger
from database import CalendarAccount, UserEvent
from sqlalchemy.ext.asyncio import AsyncSession

class YandexCalendarAPI:
    def __init__(self, email: str, app_password:str):
        self.url = "https://caldav.yandex.ru"
        self.email = email
        self.password = app_password

        
    async def get_events(self, start, end):
        try:
            async with await aio.get_calendar(
                url=self.url, 
                username=self.email, 
                password=self.password
            ) as calendar:
                events = await calendar.search(event=True, start=start, end=end, expand=True)
                return events
        except Exception as e:
            logger.exception(f"YandexCalendarAPI | {e}")
            return "ОШИБКА: Не удалось получить события"

    async def get_day_events(self, date: str):
        date = datetime.fromisoformat(date)
        end_of_day = date.replace(hour=23, minute=59, second=59)
        return await self.get_events(date, end_of_day)

    async def get_week_events(self, client, date: str):
        date = datetime.fromisoformat(date)
        days_to_sunday = 6 - date.weekday()
        end_of_week = date + datetime.timedelta(days=days_to_sunday)
        end_of_week = end_of_week.replace(hour=23, minute=59, second=59)
        return await self.get_events(client, date, end_of_week)
        
    async def get_month_events(self, client, date:str):
        date = datetime.fromisoformat(date)
        _, last_day = calendar.monthrange(date.year, date.month)
        end_of_month = date.replace(day=last_day, hour=23, minute=59, second=59)
        return await self.get_events(client, date, end_of_month)


    async def sync_event(self, event: UserEvent):
        async with await aio.get_calendar(
            url=self.url, 
            username=self.email, 
            password=self.password
        ) as calendar:
            try:
                await calendar.add_event(
                    dtstart=event.start_time,
                    dtend=event.end_time,
                    summary=event.title,
                    description=event.description
                )
                return True
            except Exception as e:
                logger.exception(f"YandexCalendarAPI | {e}")
                return False
