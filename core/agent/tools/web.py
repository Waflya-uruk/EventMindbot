
import json
import re
import requests

from typing import Optional
from bs4 import BeautifulSoup
from datetime import datetime, timedelta, timezone

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

    def _clean_and_parse(date_str: str) -> Optional[datetime]:
        if not date_str:
            return None
        date_str = str(date_str).strip().replace("Z", "")
        
        for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue
        
        match_ru = re.search(r"(\d{1,2})[\./_-](\d{1,2})[\./_-](\d{2,4})", date_str)
        if match_ru:
            day, month, year = match_ru.groups()
            if len(year) == 2:
                year = f"20{year}"
            try:
                return datetime(int(year), int(month), int(day), 12, 0, 0)
            except ValueError:
                pass
        return None

    try:
        odoo = _get_client()
        EventModel = odoo.env["event.event"]

        existing_by_url = EventModel.search([("description", "like", url)])
        if existing_by_url:
            return f"Пропущено: Мероприятие из источника {url} уже импортировано ранее (ID: {existing_by_url[0]})."

        response = requests.get(
            url,
            timeout=10,
            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"},
        )
        if response.status_code != 200:
            return f"Не удалось загрузить страницу. Статус код: {response.status_code}"

        response.encoding = response.apparent_encoding
        soup = BeautifulSoup(response.text, "html.parser")
        
        scripts = soup.find_all("script", type="application/ld+json")
        event_data = None
        for script in scripts:
            try:
                data = json.loads(script.string)
                if isinstance(data, dict) and data.get("@type") == "Event":
                    event_data = data
                    break
            except:
                continue

        name = "Мероприятие из внешнего источника"
        site_description = ""
        raw_start = None
        raw_end = None

        if event_data:
            name = event_data.get("name", name)
            raw_start = event_data.get("startDate")
            raw_end = event_data.get("endDate")
            site_description = event_data.get("description", "")
        else:
            og_title = soup.find("meta", property="og:title")
            if og_title and og_title.get("content"):
                name = og_title["content"].strip()
            elif soup.title and soup.title.string:
                name = soup.title.string.strip()

            time_tag = soup.find("time")
            if time_tag and time_tag.get("datetime"):
                raw_start = time_tag["datetime"]
            
            if not raw_start:
                page_text = soup.get_text()
                
                months_map = {
                    "янв": "01", "фев": "02", "мар": "03", "апр": "04", 
                    "май": "05", "мая": "05", "июн": "06", "июл": "07", 
                    "авг": "08", "сен": "09", "окт": "10", "ноя": "11", "дек": "12"
                }
                
                text_date_match = re.search(
                    r"(\d{1,2})\s+(янв|фев|мар|апр|май|мая|июн|июл|авг|сен|окт|ноя|дек)[а-я]*\s*(\d{4})?", 
                    page_text.lower()
                )
                match_digits = re.search(r"(\d{1,2})[\./_-](\d{1,2})[\./_-](\d{2,4})", page_text)
                
                if text_date_match:
                    day, month_word, year = text_date_match.groups()
                    month = months_map[month_word[:3]]
                    year = year if year else "2026"
                    raw_start = f"{year}-{month}-{day.zfill(2)}T12:00:00"
                elif match_digits:
                    raw_start = match_digits.group(0)

        if not raw_start and suggested_date_begin:
            raw_start = suggested_date_begin
        if not raw_end and suggested_date_end:
            raw_end = suggested_date_end

        parsed_start = _clean_and_parse(raw_start)
        parsed_end = _clean_and_parse(raw_end)

        if not parsed_start:
            parsed_start = datetime.now(timezone.utc)
        if not parsed_end:
            parsed_end = parsed_start + timedelta(hours=2)

        start_dt = parsed_start.strftime("%Y-%m-%d %H:%M:%S")
        end_dt = parsed_end.strftime("%Y-%m-%d %H:%M:%S")

        existing_by_name = EventModel.search([("name", "=", name)])
        if existing_by_name:
            return f"Пропущено: Мероприятие с названием '{name}' уже существует в системе (ID: {existing_by_name[0]})."

        if not site_description:
            meta_desc = soup.find("meta", property="og:description") or soup.find("meta", attrs={"name": "description"})
            if meta_desc and meta_desc.get("content"):
                site_description = meta_desc["content"].strip()

        if not site_description or len(site_description) < 100:
            paragraphs = [
                p.get_text().strip() for p in soup.find_all("p") 
                if len(p.get_text().strip()) > 40
            ]
            if paragraphs:
                site_description = "\n\n".join(paragraphs[:5])

        description_blocks = []

        if custom_description and custom_description.strip():
            description_blocks.append(f"<b>Анонс от EventMind:</b><br/>{custom_description.strip()}")

        if site_description and site_description.strip():
            formatted_site_desc = site_description.replace("\n", "<br/>")
            description_blocks.append(f"<b>Детальная информация с сайта:</b><br/>{formatted_site_desc}")

        if description_blocks:
            full_html_description = "<br/><br/>".join(description_blocks) + f"<br/><br/><p><b>Источник:</b> <a href='{url}' target='_blank'>{url}</a></p>"
        else:
            full_html_description = f"<p>Детальное описание отсутствует.</p><br/><p><b>Источник:</b> <a href='{url}' target='_blank'>{url}</a></p>"

        new_event_id = EventModel.create({
            "name": name,
            "date_begin": start_dt,
            "date_end": end_dt,
            "description": full_html_description,
            "is_published": True,
        })

        return f"Успешно спарсено и добавлено в Odoo! Название: '{name}', ID: {new_event_id}."

    except Exception as e:
        return f"Критическая ошибка при парсинге или импорте: {str(e)}"
