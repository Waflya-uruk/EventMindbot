import logging
import sys

from dotenv import load_dotenv
load_dotenv()

from database import init_db
from fastapi import FastAPI
from contextlib import asynccontextmanager
from services.routers import calendars_router, chat_router, login_router, registration_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger("eventmind")

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

@app.get("/health")
def health_check():
    return {"status": "ok", "message": "EventMind is alive"}
