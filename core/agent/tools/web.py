
import json
from typing import Optional
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timezone
from langchain.tools import tool
from ddgs import DDGS
from core.agent.odoo import get_odoo_client

_get_client = get_odoo_client

@tool
def search_web_events(query: str) -> str:
    """Используй этот инструмент, чтобы искать информацию о мероприятиях в открытом интернете по ключевым словам. Возвращает список сайтов и краткое описание."""
    try:
        with DDGS(timeout=10) as ddgs:
            results = [r for r in ddgs.text(query, max_results=3)]
        if not results:
            return "По данному запросу в интернете ничего не найдено."
        
        formatted_results = []
        for r in results:
            formatted_results.append(f"Название: {r['title']}\nСсылка: {r['href']}\nОписание: {r['body']}\n---")
        return "\n".join(formatted_results)
    except Exception as e:
        return f"Предупреждение: Поиск временно недоступен: {str(e)}"

@tool
def parse_and_import_from_url(
    url: str,
    custom_description: str = "",
    suggested_date_begin: Optional[str] = None,
    suggested_date_end: Optional[str] = None,
) -> str:
    """Используй этот инструмент для автоматического парсинга страницы и добавления мероприятия в Odoo.

    Если ты знаешь примерную или точную дату из поисковой выдачи, обязательно
    передай её в suggested_date_begin и suggested_date_end (в формате YYYY-MM-DD
    или ISO).
    """
    url = url.strip().rstrip("}").strip()

    if not url.startswith(("http://", "https://")):
        return f"Ошибка: неверный формат URL: {url}"

    try:
        odoo = _get_client()
        EventModel = odoo.env["event.event"]

        existing_by_url = EventModel.search(
            [("description", "like", url)]
        )
        if existing_by_url:
            return f"Пропущено: Мероприятие из источника {url} уже импортировано ранее (ID: {existing_by_url[0]})."

        response = requests.get(
            url,
            timeout=10,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
            },
        )
        if response.status_code != 200:
            return f"Не удалось загрузить страницу. Статус код: {response.status_code}"

        response.encoding = response.apparent_encoding
        soup = BeautifulSoup(response.text, "html.parser")

        scripts = soup.find_all(
            "script", type="application/ld+json"
        )
        event_data = None
        for script in scripts:
            try:
                data = json.loads(script.string)
                if (
                    isinstance(data, dict)
                    and data.get("@type") == "Event"
                ):
                    event_data = data
                    break
            except:
                continue

        name = "Мероприятие из внешнего источника"
        site_description = ""
        start_str = None
        end_str = None

        if event_data:
            name = event_data.get("name", name)
            start_str = event_data.get("startDate")
            end_str = event_data.get("endDate")
            site_description = event_data.get("description", "")
        else:
            og_title = soup.find("meta", property="og:title")
            if og_title and og_title.get("content"):
                name = og_title["content"].strip()
            elif soup.title and soup.title.string:
                name = soup.title.string.strip()

        if not start_str and suggested_date_begin:
            start_str = suggested_date_begin
        if not end_str and suggested_date_end:
            end_str = suggested_date_end or start_str

        if not start_str:
            start_str = datetime.now(timezone.utc).isoformat()
        if not end_str:
            end_str = start_str

        existing_by_name = EventModel.search([("name", "=", name)])
        if existing_by_name:
            return f"Пропущено: Мероприятие с названием '{name}' уже существует в системе (ID: {existing_by_name[0]})."

        if not site_description:
            meta_desc = soup.find(
                "meta", property="og:description"
            ) or soup.find("meta", attrs={"name": "description"})
            if meta_desc and meta_desc.get("content"):
                site_description = meta_desc["content"].strip()

        final_text_desc = (
            site_description if site_description else custom_description
        )
        if not final_text_desc:
            final_text_desc = "Детальное описание отсутствует."

        full_html_description = f"<p>{final_text_desc}</p><br/><p><b>Источник:</b> <a href='{url}' target='_blank'>{url}</a></p>"

        try:
            start_dt = datetime.fromisoformat(
                start_str.replace("Z", "+00:00")
            ).strftime("%Y-%m-%d %H:%M:%S")
            end_dt = datetime.fromisoformat(
                end_str.replace("Z", "+00:00")
            ).strftime("%Y-%m-%d %H:%M:%S")
        except:
            start_dt = datetime.now(timezone.utc).strftime(
                "%Y-%m-%d %H:%M:%S"
            )
            end_dt = datetime.now(timezone.utc).strftime(
                "%Y-%m-%d %H:%M:%S"
            )

        new_event_id = EventModel.create(
            {
                "name": name,
                "date_begin": start_dt,
                "date_end": end_dt,
                "description": full_html_description,
                "is_published": True,
            }
        )

        return f"Успешно спарсено и добавлено в Odoo! Название: '{name}', ID: {new_event_id}."

    except Exception as e:
        return (
            f"Критическая ошибка при парсинге или импорте: {str(e)}"
        )
