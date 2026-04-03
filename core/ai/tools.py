from datetime import datetime

from langchain.tools import tool
from langchain_core.runnables import RunnableConfig

from database import create_event, get_calendars_by_id, AsyncSessionLocal
from services.api.calendar_api import YandexCalendarAPI
from core.logs import logger

@tool
async def create_calendar_event(
    title: str,
    description:str, 
    start_time: str, 
    end_time:str, 
    category:str, 
    config: RunnableConfig
):
    """
    Создает новое событие в календаре и фиксирует его в логе активности для будущих рекомендаций.
    
    Аргументы:
    - title: Краткое название события.
    - description: Детальное описание (что именно нужно сделать).
    - start_time: Время начала в формате ISO 8601 (ГГГГ-ММ-ДДTHH:MM:SSZ). 
                 ВАЖНО: Всегда используй UTC время.
    - end_time: Время окончания в формате ISO 8601 (UTC).
    - category: Категория дела (например: 'Work', 'Sport', 'Education', 'Rest', 'Hobby').
    """

    user_id = config.get("configurable", {}).get("user_id")
    if not user_id:
        return "ОШИБКА: Не удалось определить пользователя."
    
    async with AsyncSessionLocal() as db:
        try:
            accounts = await get_calendars_by_id(db, user_id=user_id)
            if not accounts:
                return "ОСТАНОВИСЬ. Календари отсутствуют. Сообщи об этом пользователю."
            dt_start = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
            dt_end = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
            
            new_event = await create_event(db, user_id, title, description, dt_start, dt_end)
            
            results = []
            bad_emails = []
            for account in accounts:
                calendar = YandexCalendarAPI(account.email, account.app_password)
                synced = await calendar.sync_event(new_event)
                results.append(synced)
                if not synced:
                    bad_emails.append(account.email)

            if all(results) and len(results) > 0:
                new_event.sync_status = "synced"
            await db.commit()
            
            if bad_emails:
                report = f"ОСТАНОВИСЬ. Не удалось отправить мероприятие на: {bad_emails}. Сообщи это пользователю."
            else:
                report = "ОСТАНОВИСЬ. Мероприятие успешно внесено. Сообщи это пользователю."

            return report
        except Exception as e:
            logger.exception(f"AI Tools | {e}") 
            return f"ОСТАНОВИСЬ. Неизвестная ошибка. Сообщи об этом пользователю."


@tool
async def check_calendar_events(
    start_date: str,
    end_date: str,
    config: RunnableConfig
):
    """
    Получает список всех запланированных событий из подключенных календарей пользователя за указанный период.
    Используй эту функцию перед планированием новых задач, чтобы избежать конфликтов, 
    или для анализа текущей загруженности пользователя.

    Аргументы:
    - start_date: Начало периода поиска в формате ISO 8601 (ГГГГ-ММ-ДД). 
                  Включает события, начинающиеся с 00:00:00 UTC этого дня.
    - end_date: Конец периода поиска в формате ISO 8601 (ГГГГ-ММ-ДД). 
                Включает события до 23:59:59 UTC этого дня.

    Возвращает:
    Список словарей с деталями событий:
    [
        {
            "title": "Название",
            "start": "ISO_TIMESTAMP",
            "end": "ISO_TIMESTAMP",
            "description": "Описание"
        }, ...
    ]

    Инструкция для Агента:
    1. Всегда проверяй этот список перед тем, как предложить пользователю время для новой задачи.
    2. Если список пуст, значит день свободен.
    """
    user_id = config.get("configurable", {}).get("user_id")
    if not user_id:
        return "ОШИБКА: Не удалось определить пользователя."
    
    async with AsyncSessionLocal() as db:
        try:
            accounts = await get_calendars_by_id(db, user_id=user_id)
            if not accounts:
                return "ОШИБКА: У пользователя не подключены календари."
            
            report = []
            calendar = YandexCalendarAPI(accounts[0].email, accounts[0].app_password)
            events = await calendar.get_events(start_date, end_date)
            for event in events:
                report.append(parse_caldav_event(event))
            
            return report
        except Exception as e:
            logger.exception(f"AI Tools | {e}") 
            return f"ОШИБКА: Неизвестная"

async def parse_caldav_event(event_obj):
    ical = event_obj.icalendar_instance
    v_event = None
    
    for component in ical.walk():
        if component.name == "VEVENT":
            v_event = component
            break
            
    if not v_event:
        return None

    return {
        "title": str(v_event.get('summary', 'Без названия')),
        "start": v_event.get('dtstart').dt.isoformat() if v_event.get('dtstart') else None,
        "end": v_event.get('dtend').dt.isoformat() if v_event.get('dtend') else None,
        "description": str(v_event.get('description', ''))
    }
            


def get_user_recommendations(user_id: int, categories: list = None):
    """Используй для поиска интересных событий на основе рейтинга авторов."""
    return "Список рекомендованных событий: ..."
