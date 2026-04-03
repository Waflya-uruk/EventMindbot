from core.logs import logger

from dotenv import load_dotenv
load_dotenv()

from database import init_db
from fastapi import FastAPI
from contextlib import asynccontextmanager
from services.routers import *



@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- КОД ПРИ ЗАПУСКЕ (Startup) ---
    try:
        await init_db()
        print("🚀 EventMind API: База данных инициализирована")
    except Exception as e:
        print(f"❌ Ошибка при старте БД: {e}")

    print("Приложение EventMind запущено, база готова")
    
    yield
    
    # --- КОД ПРИ ВЫКЛЮЧЕНИИ (Shutdown) ---
    print("👋 Приложение завершает работу")

app = FastAPI(
    title="EventMind API",
    version="0.1.0",
    lifespan=lifespan
)

app.include_router(calendars_router)
app.include_router(chat_router)
app.include_router(login_router)
app.include_router(registration_router)
app.include_router(events_router)
app.include_router(activity_router)

@app.get("/health")
def health_check():
    return {"status": "ok", "message": "EventMind is alive"}
