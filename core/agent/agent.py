import os
import warnings
from dotenv import load_dotenv
from langchain_core._api.deprecation import LangChainPendingDeprecationWarning

warnings.filterwarnings("ignore", category=LangChainPendingDeprecationWarning)
load_dotenv()

from .tools import get_public_events, create_public_event, parse_and_import_from_url, search_web_events, update_public_event
from langchain_gigachat.chat_models import GigaChat
from langchain.agents import create_agent

model = GigaChat(
    credentials=os.getenv("GIGACHAT_CREDENTIALS"), 
    verify_ssl_certs=False,
    model="GigaChat",
    scope="GIGACHAT_API_PERS",
    temperature=0.3
)

tools = [get_public_events, create_public_event, parse_and_import_from_url, search_web_events, update_public_event]

system_prompt = """
Роль: ИИ-агент EventMind для поиска IT-мероприятий и их импорта в Odoo.
Контекст: июнь 2026 года. Целевой год: 2026 и будущее.

АЛГОРИТМ:
1. Сформировать поисковый запрос (кнопка поиска `search_web_events`).
2. Отфильтровать выдачу, отсекая мусор и архивы.
3. Извлечь дату из сниппета по ПРАВИЛАМ ДАТ.
4. Вызвать импорт `parse_and_import_from_url`.

ПРАВИЛА ПОИСКА И ФИЛЬТРАЦИИ:
- Формат запроса: "[Тема] 2026 [маркер: конференция/митап/хакатон/регистрация] -2023 -2024 -2025 -wikipedia -википедия -статья -обзор -новости"
- ИГНОРИРОВАТЬ: ссылки прошлых лет (2024, 2025), отчеты/итоги, статьи ("что такое", "как сделать"), блоги (habr, vc, medium, wikipedia).
- ПАРСИТЬ: только лендинги будущих событий 2026 года с регистрацией или программой.

ПРАВИЛА ДАТ (Интерпретация перед вызовом парсера в YYYY-MM-DD):
1. Грязный формат ("19_09_26", "19-09-26") -> `suggested_date_begin='2026-09-19'`. Год "26" всегда разворачивать в "2026".
2. Диапазоны ("25-26 мая") -> `suggested_date_begin='2026-05-25'`, `suggested_date_end='2026-05-26'`.
3. Относительные ("в конце июля") -> Считать от июня 2026 -> `suggested_date_begin='2026-07-25'`.

ПРИМЕРЫ:
- Сниппет: "Что такое ИИ..." или "Итоги митапа 2025..." -> ПРОПУСТИТЬ.
- Сниппет: "Msk AI-Fest пройдет 05_12_26. Регистрация..." -> Вызвать `parse_and_import_from_url(url='...', suggested_date_begin='2026-12-05')`.

ОТВЕТ: Только маркированный список добавленных событий с их Odoo ID. Без лишних слов.
"""

agent = create_agent(
    model=model,
    tools=tools,
    system_prompt=system_prompt
)

if __name__ == "__main__":
    print("🚀 Запуск проверки ИИ-агента...")
    
    print("\nПроверка запроса списка мероприятий:")
    try:
        response_read = agent.invoke({"messages": [{"role": "user", "content": "Какие мероприятия сейчас есть на сайте?"}]})
        
        messages = response_read.get("messages", [])
        if messages:
            final_text = messages[-1].content
            print("\n🤖 Ответ ассистента:")
            print(final_text)
        else:
            print("Ответ пуст.")
            
    except Exception as e:
        print(f"Ошибка при тесте чтения: {e}")
    
    print("Проверка создания нового мероприятия:")
    try:
        response_create = agent.invoke({"messages": [{"role": "user", "content": "Организуй открытый вебинар по машинному обучению на 150 человек 20 июня 2026 года в 18:00 на полтора часа"}]})
        messages = response_create.get("messages", [])
        if messages:
            final_text = messages[-1].content
            print("\n🤖 Ответ ассистента:")
            print(final_text)
        else:
            print("Ответ пуст.")
    except Exception as e:
        print(f"Ошибка при тесте создания: {e}")
