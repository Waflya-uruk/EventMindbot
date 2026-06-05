from datetime import datetime, timezone
from typing import Optional
from langchain.tools import tool

from core.agent.odoo import get_odoo_client
_get_client = get_odoo_client




def _find_or_create_location(odoo, location_name: str) -> Optional[int]:
    """Вспомогательная функция: ищет локацию в Odoo (res.

    partner) или создает новую, если не нашла.
    """
    if not location_name:
        return None
    PartnerModel = odoo.env["res.partner"]
    existing_partner = PartnerModel.search(
        [("name", "=", location_name.strip())], limit=1
    )
    if existing_partner:
        return existing_partner[0]
    return PartnerModel.create({"name": location_name.strip()})


@tool
def get_public_events(date_from: str = None, limit: int = 5) -> str:
    """Используй этот инструмент, чтобы узнать расписание публичных мероприятий, вебинаров или лекций из модуля website_event.

    Показывает ID, время и место проведения.
    """
    try:
        odoo = _get_client()
        EventModel = odoo.env["event.event"]
        domain = []

        if date_from:
            domain.append(
                ("date_begin", ">=", f"{date_from} 00:00:00")
            )
        else:
            now_str = datetime.now(timezone.utc).strftime(
                "%Y-%m-%d %H:%M:%S"
            )
            domain.append(("date_begin", ">=", now_str))

        event_ids = EventModel.search(
            domain, limit=limit, order="date_begin ASC"
        )
        if not event_ids:
            return "Публичных мероприятий на указанный период не найдено."

        events = EventModel.browse(event_ids)
        result = []
        for ev in events:
            seats_info = (
                f"Свободно мест: {ev.seats_available} из {ev.seats_max}"
                if ev.seats_max > 0
                else "Места не ограничены"
            )
            location = (
                ev.address_id.name if ev.address_id else "Не указано"
            )

            result.append(
                f"- [ID: {ev.id}] '{ev.name}' | "
                f"Начало: {ev.date_begin} UTC | Окончание: {ev.date_end} UTC | "
                f"Место: {location} | {seats_info}"
            )
        return (
            "Список найденных публичных мероприятий:\n"
            + "\n".join(result)
        )
    except Exception as e:
        return f"Ошибка при получении списка мероприятий из Odoo: {str(e)}"


@tool
def create_public_event(
    name: str,
    date_begin: str,
    date_end: str,
    location_name: Optional[str] = None,
    seats_max: int = 0,
) -> str:
    """Используй этот инструмент, когда пользователь просит создать, запланировать или опубликовать новое мероприятие.

    Можно сразу указать место проведения (location_name).
    """
    try:
        start_dt = datetime.fromisoformat(
            date_begin.replace("Z", "")
        ).strftime("%Y-%m-%d %H:%M:%S")
        end_dt = datetime.fromisoformat(
            date_end.replace("Z", "")
        ).strftime("%Y-%m-%d %H:%M:%S")

        odoo = _get_client()
        EventModel = odoo.env["event.event"]

        event_vals = {
            "name": name,
            "date_begin": start_dt,
            "date_end": end_dt,
            "seats_max": seats_max,
            "is_published": True,
        }

        if location_name:
            address_id = _find_or_create_location(
                odoo, location_name
            )
            if address_id:
                event_vals["address_id"] = address_id

        new_event_id = EventModel.create(event_vals)
        seats_text = (
            f"Лимит мест: {seats_max}"
            if seats_max > 0
            else "Без лимита"
        )
        loc_text = (
            f"Место: {location_name}"
            if location_name
            else "Место не указано"
        )

        return f"Успех! Публичное мероприятие '{name}' создано (ID: {new_event_id}). {loc_text}. {seats_text}."
    except Exception as e:
        return (
            f"Не удалось создать мероприятие в Odoo. Ошибка: {str(e)}"
        )


@tool
def update_public_event(
    event_id: int,
    date_begin: Optional[str] = None,
    date_end: Optional[str] = None,
    location_name: Optional[str] = None,
) -> str:
    """Используй этот инструмент, чтобы ИЗМЕНИТЬ (перенести) время проведения или поменять МЕСТО (локацию) у уже существующего мероприятия по его ID.

    Передавай только те параметры, которые нужно изменить.
    """
    try:
        odoo = _get_client()
        EventModel = odoo.env["event.event"]

        if not EventModel.search([("id", "=", event_id)]):
            return f"Ошибка: Мероприятие с ID {event_id} не найдено в системе."

        update_vals = {}

        if date_begin:
            update_vals["date_begin"] = datetime.fromisoformat(
                date_begin.replace("Z", "")
            ).strftime("%Y-%m-%d %H:%M:%S")

        if date_end:
            update_vals["date_end"] = datetime.fromisoformat(
                date_end.replace("Z", "")
            ).strftime("%Y-%m-%d %H:%M:%S")

        if location_name:
            address_id = _find_or_create_location(
                odoo, location_name
            )
            if address_id:
                update_vals["address_id"] = address_id

        if not update_vals:
            return "Предупреждение: Не передано никаких данных для изменения."

        EventModel.write([event_id], update_vals)

        return f"Успешно! Мероприятие с ID {event_id} обновлено. Измененные параметры: {list(update_vals.keys())}."
    except Exception as e:
        return f"Не удалось обновить мероприятие {event_id}. Ошибка: {str(e)}"
