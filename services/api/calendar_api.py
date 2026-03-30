import asyncio
from caldav import aio
import calendar
from datetime import datetime

from sqlalchemy import select

from database.database import CalendarAccount, UserEvent
from sqlalchemy.ext.asyncio import AsyncSession

class YandexCalendarAPI:
    def __init__(self, email: str, app_password:str):
        self.url = "https://caldav.yandex.ru"
        self.email = email
        self.password = app_password

        
    async def get_events(self, start, end):
        async with await aio.get_calendar(
            url=self.url, 
            username=self.email, 
            password=self.password
        ) as calendar:
            events = await calendar.search(event=True, start=start, end=end, expand=True)
            return events

    async def get_day_events(self, now_date: str):
        now_date = datetime.fromisoformat(now_date)
        end_of_day = now_date.replace(hour=23, minute=59, second=59)
        return await self.get_events(now_date, end_of_day)

    async def get_week_events(self, client, now_date: str):
        now_date = datetime.fromisoformat(now_date)
        days_to_sunday = 6 - now_date.weekday()
        end_of_week = now_date + datetime.timedelta(days=days_to_sunday)
        end_of_week = end_of_week.replace(hour=23, minute=59, second=59)
        return await self.get_events(client, now_date, end_of_week)
        
    async def get_month_events(self, client, now_date:str):
        now_date = datetime.fromisoformat(now_date)
        _, last_day = calendar.monthrange(now_date.year, now_date.month)
        end_of_month = now_date.replace(day=last_day, hour=23, minute=59, second=59)
        return await self.get_events(client, now_date, end_of_month)


    async def sync_events(self, db: AsyncSession):
        query = select(UserEvent).filter_by(sync_status="pending")
        result = await db.execute(query)
        pending_events = result.scalars().all()

        for event in pending_events:
            query = select(CalendarAccount).filter_by(user_id=event.user_id)
            result = await db.execute(query)
            accounts = result.scalars().all()
            for account in accounts:
                if not account:
                    print(f"У пользователя {event.user_id} не подключен календарь")
                    continue

                # YANDEX
                print(f"Отправляем '{event.title}' в Яндекс...")
                data = {
                    'title': event.title,
                    'description': event.description,
                    'start': event.start_time,
                    'end': event.end_time
                }

                send = self.send_event(data)
                if send:
                    event.sync_status = "synced"
        await db.commit()
        return send

    async def send_event(self, event_data):
        '''
        ```python \n
        event_data = {
            'title': 'Мастер-класс от Автора',
            'description': 'Интересное событие из нашей ленты',
            'start': datetime.now() + timedelta(hours=2),
            'end': datetime.now() + timedelta(hours=3)
        }
        sync_with_yandex(get_client(*,*), event_data)
        ```'''
        
        async with await aio.get_calendar(
            url=self.url, 
            username=self.email, 
            password=self.password
        ) as calendar:
            new_event = await calendar.add_event(
                dtstart=event_data['start'],
                dtend=event_data['end'],
                summary=event_data['title'],
                description=event_data['description']
            )
            return f"✅ Событие создано: {new_event.url}"
