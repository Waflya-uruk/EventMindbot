from datetime import datetime, timezone
from typing import  Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from core.agent import *

router = APIRouter(
    prefix="/chat",
    tags=["Chat"]
)

class ChatRequest(BaseModel):
    message: str
    timestamp: Optional[str] = None
    user_id: int

@router.post("/")
async def chat_endpoint(request: ChatRequest):
    try:
        current_date = datetime.now(timezone.utc).isoformat()
        message = f"Контекст: Сегодня {current_date}.  Сообщение пользователя: {request.message}"

        input = {"messages": [{"role": "user", "content": message}]}

        config = {"configurable": {"user_id": request.user_id}, "recursion_limit": 4}

        response = await agent.ainvoke(input=input, config=config)

        messages = response["messages"]
        response_text = messages[-1].content

        return {
            "reply": response_text
        }
    except Exception as e:
        print(f"Ошибка Агента: {e}")
        raise HTTPException(status_code=500, detail="Агент временно недоступен")
