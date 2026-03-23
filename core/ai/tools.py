import traceback

from langchain.tools import tool
from langchain_core.runnables import RunnableConfig

from database.database import SessionLocal
from database.service import create_event, get_user_calendars
from services.api.calendar_api import get_client, get_day_events, sync_events

@tool
def create_calendar_event(title: str, description:str, start_time: str, end_time:str, config: RunnableConfig):
    """
    Используй эту функцию, когда пользователь просит запланировать что-то.
    start_time и end_time должен быть в формате ISO (ГГГГ-ММ-ДД ТТ:ММ).
    """
    user_id = config.get("configurable", {}).get("user_id")
    if not user_id:
        return "Ошибка: не удалось определить пользователя."
    
    try:
        with SessionLocal() as db:
            accounts = get_user_calendars(db, user_id=user_id)
            if not accounts:
                return "Ошибка: У тебя не подключены календари."
            
            create_event(db, user_id, title, description, start_time, end_time)
            result = sync_events() 

            return result
    except Exception as e:
        print(f"Full error for dev: {traceback.format_exc()}") 
        return f"ОШИБКА: {type(e).__name__} - {str(e)}"




def check_schedule(date: str, config: RunnableConfig):
    """
    Проверяет расписание пользователя на конкретную дату.
    date должен быть в формате ГГГГ-ММ-ДД. Если не указан — проверяет на сегодня.
    """
    user_id = config.get("configurable", {}).get("user_id")
    if not user_id:
        return "Ошибка: не удалось определить пользователя."
    
    try:
        accounts = get_user_calendars(user_id)
        if not accounts:
            return "Отсутствуют созданные календари"
        
        all_events = []

        client = get_client()
        events = get_day_events(client, date)
        
        for account in accounts:
            for event in events:
                time_str = event['start'].strftime('%H:%M') if hasattr(event['start'], 'strftime') else "Весь день"
                all_events.append(f"[{account.provider}] {time_str} - {event['title']}")

        if not all_events:
            return "На сегодня в календарях пусто."
        return "Полное расписание на сегодня:\n" + "\n".join(all_events)
    except Exception as e:
        return f"Ошибка при проверке расписания: {str(e)}"


def get_user_recommendations(user_id: int, categories: list = None):
    """Используй для поиска интересных событий на основе рейтинга авторов."""
    # Вызываешь твою функцию get_recommendations(db_session, categories=categories)
    return "Список рекомендованных событий: ..."

@tool
def check_user_calendars(config: RunnableConfig):
    """Проверяет, какие календари (Яндекс/Google) подключены у пользователя."""
    user_id = config.get("configurable", {}).get("user_id")
    if not user_id:
        return "Ошибка: не удалось определить пользователя."
    
    with SessionLocal() as db:
        accounts = get_user_calendars(db, user_id)
        if not accounts:
            return "У пользователя нет подключенных календарей."
    return [f"{acc.provider}: {acc.email}" for acc in accounts]