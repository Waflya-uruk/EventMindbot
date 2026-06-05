from dotenv import load_dotenv
load_dotenv()

from core.agent import agent

def run_proactive_search():
    user_interests = ["Здоровье", "Наука", "Разработка игр", "Фитнес"]
    interests_str = ", ".join(user_interests)
    
    #task_input = f"https://pmlconf.yandex.ru/2026/ автоматически добавь мероприятие в нашу систему Odoo пометив в описании что они найдены ии агентом."
    task_input = f"Интересы пользователя: {interests_str}. Найди в интернете новые релевантные ИТ-мероприятия, конференции или лекции на ближайшие месяцы 2026 года и автоматически добавь их в нашу систему Odoo пометив в описании что они найдены ии агентом."
    
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

if __name__ == "__main__":
    run_proactive_search()
