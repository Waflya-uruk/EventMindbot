from dotenv import load_dotenv
load_dotenv()

from core.agent import agent

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from services.routers import chat_router

app = FastAPI(
    title="EventMind AI Agent Service",
    description="Микросервис ИИ-агента для интеграции с Odoo",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat_router)

@app.get("/health")
def health_check():
    """Эндпоинт для проверки работоспособности сервиса (healthcheck)"""
    return {"status": "healthy", "service": "agent"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False)




def run_proactive_search():
    user_interests = ["Здоровье", "Наука", "Разработка игр", "Фитнес"]
    interests_str = ", ".join(user_interests)
    
    #task_input = f"https://pmlconf.yandex.ru/2026/ автоматически добавь мероприятие в нашу систему Odoo пометив в описании что они найдены ии агентом."
    task_input = f"Интересы пользователя: {interests_str}. Найди в интернете новые релевантные мероприятия, конференции или лекции на ближайшие месяцы 2026 года и автоматически добавь их в нашу систему Odoo пометив в описании что они найдены ии агентом."
    
    try:
        response = agent.invoke(
            {"messages": [{"role": "user", "content": task_input}]}
        )
        messages = response.get("messages", [])

        if messages:
            print("=== ХРОНОЛОГИЯ РАБОТЫ АГЕНТА ===")
            for msg in messages:
                if (
                    hasattr(msg, "tool_calls")
                    and msg.tool_calls
                ):
                    print(
                        f"\n🤖 Робот вызывает инструмент: {msg.tool_calls[0]['name']}"
                    )
                    print(
                        f"   Аргументы: {msg.tool_calls[0]['args']}"
                    )

                elif (
                    msg.type == "tool"
                ):
                    print(
                        f"🛠️ Ответ инструмента (ID: {msg.tool_call_id}):"
                    )
                    print(f"   {msg.content}")

            print("\n=== ИТОГОВЫЙ ОТЧЕТ ОБ АВТОНОМНОЙ РАБОТЕ ===")
            print(messages[-1].content)

    except Exception as e:
        print(f"Ошибка при автономном поиске: {e}")
