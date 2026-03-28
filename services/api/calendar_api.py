import caldav
import calendar
import datetime

from database.database import CalendarAccount, UserEvent
from sqlalchemy.orm import Session


CALDAV_URL = "https://caldav.yandex.ru"

def get_client(email: str, app_password):
    client = caldav.DAVClient(
        url=CALDAV_URL, 
        username=email, 
        password=app_password
    )
    return client

    
def get_events(client, start, end):
    my_principal = client.principal()
    calendar = my_principal.calendars()[0]
    events = calendar.date_search(start, end)
    return events

def get_day_events(client, now_date: str):
    now_date = datetime.fromisoformat(now_date)
    end_of_day = now_date.replace(hour=23, minute=59, second=59)
    return get_events(client, now_date, end_of_day)

def get_week_events(client, now_date: str):
    now_date = datetime.fromisoformat(now_date)
    days_to_sunday = 6 - now_date.weekday()
    end_of_week = now_date + datetime.timedelta(days=days_to_sunday)
    end_of_week = end_of_week.replace(hour=23, minute=59, second=59)
    return get_events(client, now_date, end_of_week)
    
def get_month_events(client, now_date:str):
    now_date = datetime.fromisoformat(now_date)
    _, last_day = calendar.monthrange(now_date.year, now_date.month)
    end_of_month = now_date.replace(day=last_day, hour=23, minute=59, second=59)
    return get_events(client, now_date, end_of_month)



def sync_events(db: Session):
    pending_events = db.query(UserEvent).filter_by(sync_status="pending").all()

    for event in pending_events:
        accounts = db.query(CalendarAccount).filter_by(user_id=event.user_id).all()

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
            client = get_client(account.email, account.app_password)
            send = send_event(client, event_data=data)
            if send:
                event.sync_status = "synced"
    db.commit()
    return send

def send_event(client, event_data):
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
    
    try:
        principal = client.principal()
        calendars = principal.calendars()
        
        if not calendars:
            return "У пользователя нет доступных календарей."
        
        calendar = calendars[0]
        new_event = calendar.save_event(
            dtstart=event_data['start'],
            dtend=event_data['end'],
            summary=event_data['title'],
            description=event_data['description']
        )
        return f"✅ Событие создано: {new_event.url}"
    except Exception as e:
        error_str = str(e)
        if "401" in error_str or "Unauthorized" in error_str or "InvalidToken" in error_str:
            return "Токен Яндекса невалиден"
        raise e
