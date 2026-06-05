import os
import warnings
from dotenv import load_dotenv
from langchain_core._api.deprecation import LangChainPendingDeprecationWarning

warnings.filterwarnings("ignore", category=LangChainPendingDeprecationWarning)
load_dotenv()

from .tools import get_public_events, create_public_event, parse_and_import_from_url, search_web_events
from langchain_gigachat.chat_models import GigaChat
from langchain.agents import create_agent

model = GigaChat(
    credentials=os.getenv("GIGACHAT_CREDENTIALS"), 
    verify_ssl_certs=False,
    model="GigaChat",
    scope="GIGACHAT_API_PERS",
    temperature=0.3
)

tools = [get_public_events, create_public_event, parse_and_import_from_url, search_web_events]

system_prompt = """
Роль: Ты — интеллектуальный автономный ассистент EventMind. Твоя миссия: проактивно находить интересные события в интернете и импортировать их в Odoo.

Инструкции по многошаговому поиску:
1. Когда тебе передают интересы пользователя, сформируй точечный поисковый запрос (например: 'конференции по машинному обучению 2026 Москва').
2. Вызови инструмент `search_web_events` для поиска вариантов.
3. Проанализируй полученные ссылки и их описания (body). Выбери наиболее релевантные и свежие (ориентируйся на текущий год: 2026).
4. Внимательно изучи текст описания каждого найденного сайта на предмет дат проведения (например: "20 марта", "в конце июля", "15-17 июня"). 
5. Для каждой перспективной ссылки поочередно вызывай инструмент `parse_and_import_from_url`. 

КРИТИЧЕСКОЕ ПРАВИЛО ДЛЯ ДАТ:
Если в поисковом сниппете (в описании ссылки) есть упоминание даты проведения, обязательно извлеки её и передай в параметры `suggested_date_begin` и `suggested_date_end` инструмента в формате YYYY-MM-DD. 
- Если известна точная дата (например, 20 марта 2026) -> передай её точно ('2026-03-20').
- Если дата примерная (например, "в июле 2026") -> передай приблизительное начало месяца ('2026-07-01').
- Не оставляй эти поля пустыми, если текст содержит хоть какое-то указание на время проведения!

Общение: Отвечай кратко, перечисляй только успешно добавленные мероприятия с их ID.
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
