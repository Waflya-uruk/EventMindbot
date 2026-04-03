import os

from .tools import create_calendar_event
from langchain_gigachat.chat_models import GigaChat
from langchain.agents import create_agent


model = GigaChat(
    credentials=os.getenv("GIGACHAT_CREDENTIALS"), 
    verify_ssl_certs=False,
    model="GigaChat",
    scope="GIGACHAT_API_PERS"
)

tools = [create_calendar_event]
system_prompt = (
    '''
Роль: Ты — интеллектуальный ассистент EventMind. Твоя миссия: помогать пользователю организовывать жизнь, учитывая его ночной график («сова»).
Инструкции:
    Общение: Отвечай пользователю кратко, вежливо и креативно. Поддерживай его идеи. Если он хочет кодить в 2 часа ночи — похвали за продуктивность.
    Планирование: Извлеки детали (название, время, категорию). Если время размыто (например, "днем"), ставь на 14:00–16:00, учитывая поздний подъем пользователя.
    '''
)
agent = create_agent(
    model=model,
    tools=tools,
    system_prompt=system_prompt,
    debug=True)
