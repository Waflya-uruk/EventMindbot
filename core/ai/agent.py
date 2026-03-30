import os

from .tools import create_calendar_event, check_schedule
from langchain_gigachat.chat_models import GigaChat
from langchain.agents import create_agent


model = GigaChat(
    credentials=os.getenv("GIGACHAT_CREDENTIALS"), 
    verify_ssl_certs=False,
    model="GigaChat",
    scope="GIGACHAT_API_PERS",
    temperature=1
)

tools = [create_calendar_event]
system_prompt = (
    '''Ты — исполнительный ассистент приложения EventMind. Не отправляй свои мысли пользователю и не поправляй его.
    Если пользователь вводит данные с ошибками, опечатками или в неправильном формате, ты должен САМ исправить их и привести к нужному формату перед вызовом функций. 
    Никогда не проси пользователя переписать сообщение. Просто делай свою работу молча.'''
)
agent = create_agent(
    model=model,
    tools=tools,
    system_prompt=system_prompt,
    debug=True)
