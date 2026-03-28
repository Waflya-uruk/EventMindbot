from sqlalchemy.orm import Session
from core.security import verify_password
import database.database as database
from database.service import create_user, create_yandex_calendar, delete_calendar_account, get_user_by_email
from datetime import datetime
from services.api import llm_api
from fastapi import Depends, FastAPI, HTTPException, Query
from pydantic import BaseModel
from typing import List, Optional
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

class CalendarRequest(BaseModel):
    user_id: int
    email: str
    password_token: str
    save: bool

class CalendarResponse(BaseModel):
    success: bool
    message: str

class CalendarAccountResponse(BaseModel):
    email: str
    password_token: str

    class Config:
        from_attributes = True


@app.post("/chat")
async def chat_endpoint(request: ChatRequest):
    try:
        current_date = datetime.now().strftime("%Y-%m-%d %H:%M")
        message = f"Контекст: Сегодня {current_date}.  Вопрос пользователя: {request.message}"

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

@app.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest):
    try:
        with database.SessionLocal() as db:
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
    except Exception as e:
        return f"ОШИБКА: {type(e).__name__} - {str(e)}"

@app.post("/register")
async def register_user(request: RegistrationRequest):
    try:
        with database.SessionLocal() as db:
            user=get_user_by_email(db, request.email)
            
            if user:
                return {"status": "exists", "message": "Пользователь уже зарегестрирован"}
            
            new_user = create_user(db, request.name, request.email, request.password)
            
            db.refresh(new_user)
            return {"success": True, "user_id": new_user.id}
    except Exception as e:
        return f"ОШИБКА: {type(e).__name__} - {str(e)}"

@app.post("/calendar", response_model=CalendarResponse)
async def calendar_service(request: CalendarRequest):
    success = False
    result = "Неизвестная ошибка"

    try:
        with database.SessionLocal() as db:
            if request.save:
                existing_account = db.query(database.CalendarAccount).filter(
                    database.CalendarAccount.email == request.email
                ).first()

                if not existing_account:
                    try:
                        create_yandex_calendar(db, request.user_id, request.email, request.password_token)
                        success = True
                        result = "Календарь успешно создан и привязан"
                    except Exception as e:
                        db.rollback()
                        result = f"Ошибка при создании: {str(e)}"
                else:
                    success = False
                    result = "Ошибка: календарь с таким email уже зарегистрирован"
            else:
                success = delete_calendar_account(db, request.email)
                if success:
                    result = "Аккаунт успешно удален"
                else:
                    result = "Ошибка: аккаунт не найден"

            return {"success": success, "message": result}
    except Exception as e:
        return f"ОШИБКА: {type(e).__name__} - {str(e)}"

@app.get("/calendars", response_model=List[CalendarAccountResponse])
async def get_calendars(user_id: int = Query()):
    try:
        with database.SessionLocal() as db:
            accounts = db.query(database.CalendarAccount).filter(
                database.CalendarAccount.user_id == user_id).all()
            return accounts
    except Exception as e:
        return f"ОШИБКА: {type(e).__name__} - {str(e)}"
