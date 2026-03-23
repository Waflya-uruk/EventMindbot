from sqlalchemy.orm import Session
from core.security import verify_password
import database.database as database
from database.service import create_user, get_user_by_email
from datetime import datetime
from services.api import llm_api
from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
from contextlib import asynccontextmanager
from dotenv import load_dotenv
from core.ai.agent import agent
from langchain.messages import HumanMessage

load_dotenv()



@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- КОД ПРИ ЗАПУСКЕ (Startup) ---
    database.init_db()
    print("Приложение EventMind запущено, база готова")
    
    yield
    
    # --- КОД ПРИ ВЫКЛЮЧЕНИИ (Shutdown) ---
    print("Приложение завершает работу")

# Привязываем lifespan к приложению
app = FastAPI(lifespan=lifespan)



class ChatRequest(BaseModel):
    message: str
    timestamp: Optional[str] = None
    user_id: int

class LoginRequest(BaseModel):
    email: str
    password: str

class LoginResponse(BaseModel):
    success: bool
    user_id: int

class RegistrationRequest(BaseModel):
    name: str
    email: str
    password: str



@app.post("/chat")
async def chat_endpoint(request: ChatRequest):
    try:
        current_date = datetime.now().strftime("%Y-%m-%d %H:%M")
        message = f"Контекст: Сегодня {current_date}.  Вопрос пользователя: {request.message}"

        input = {"messages": [{"role": "user", "content": message}]}

        config = {"configurable": {"user_id": request.user_id}}

        response = await agent.ainvoke(input=input, config=config)

        messages = response["messages"]
        response_text = messages[-1].content

        return {
            "reply": response_text
        }
    except Exception as e:
        print(f"Ошибка Агента: {e}")
        raise HTTPException(status_code=500, detail="Агент временно недоступен")

@app.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest, db: Session = Depends(database.get_db)):
    user = get_user_by_email(db, request.email)

    if not user or not verify_password(request.password, user.password_hash):
        raise HTTPException(
            status_code=401, 
            detail="Неверный email или пароль"
        )

    return {
        "success": True,
        "user_id": user.id
    }

@app.post("/register")
async def register_user(user_data: RegistrationRequest, db: Session = Depends(database.get_db)):

    user=get_user_by_email(db, user_data.email)
    
    if user:
        return {"status": "exists", "message": "Пользователь уже зарегестрирован"}
    
    new_user = create_user(db, user_data.name, user_data.email, user_data.password)
    
    db.refresh(new_user)
    return {"status": "success", "user_id": new_user.id}

# Запуск: uvicorn main:app --host 0.0.0.0 --port 8000

#user.create_user('deryagin.dim2015@yandex.ru', '27052005')
#user.create_yandex_account(1, 'deryagin.dim2015@yandex.ru', 'tfnqwznyujhropmo')

async def process_voice_event(text: str):
    """
    Полный цикл: Голос -> Текст -> AI JSON -> База данных
    """
    print("🎙 Начинаю обработку аудио...")
    
    prompt = llm_api.get_json_promt(text)
    
    print("🤖 Нейросеть формирует событие...")
    json_ai = await llm_api.get_json_from_ai(prompt)

    print("🤖 Обработка ответа нейросети")
    data = llm_api.clean_and_parse_json(json_ai)
    
    if data:
        print(f"✅ Событие распознано: {data['title']}")

        start_dt = datetime.fromisoformat(data['start_time'])
        end_dt = datetime.fromisoformat(data['end_time'])

        database.create_event(
            user_id=1, 
            title=data["title"], 
            description=data["description"], 
            start_time=start_dt, 
            end_time=end_dt
        )
        
        database.sync_events()
        print("📅 Синхронизация с календарем завершена!")
        return True
    else:
        print("❌ Не удалось распознать данные из JSON")
        return False


