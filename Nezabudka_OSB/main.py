from fastapi import FastAPI, Body, HTTPException, WebSocket, Request
from app.backend.db import engine, Base
from app.routers import result_tasks, tasks_osb
from app.pages.router import router as router_pages
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from fastapi.staticfiles import StaticFiles
from typing import List
from loguru import logger
import logging

# Настройка Loguru
logger.add(
    "logs/app.log",
    rotation="10 MB",          # Ротация при достижении 10 МБ
    retention="30 days",      # Хранить логи 30 дней
    compression="zip",        # Сжимать старые логи
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}",
    backtrace=True,           # Для детального traceback
    diagnose=True            # Доп. диагностика
)

# Отключаем стандартные логи Uvicorn
logging.getLogger("uvicorn").handlers = []
logging.getLogger("uvicorn.access").handlers = []

app = FastAPI(swagger_ui_parameters={"tryItOutEnabled": True}, debug=True)

# Middleware для логирования запросов
@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger.info(f"Request: {request.method} {request.url}")
    try:
        response = await call_next(request)
        logger.success(f"Response: {response.status_code}")
        return response
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        raise

templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")
app.include_router(result_tasks.router)
app.include_router(tasks_osb.router)

Base.metadata.create_all(bind=engine)
app.include_router(router_pages)

# WebSocket логирование
clients: List[WebSocket] = []

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    clients.append(websocket)
    logger.info("New WebSocket connection")
    try:
        while True:
            data = await websocket.receive_text()
            logger.debug(f"WebSocket message: {data}")
    except Exception as e:
        clients.remove(websocket)
        logger.error(f"WebSocket error: {e}")

@app.get("/")
async def Welcome():
    logger.info("Root endpoint accessed")
    return {"message": "Welcome to Taskmanager"}

class Result(BaseModel):
    id: int
    name_user: str

# Пример логирования в роутерах
@app.post("/results/")
async def create_result(result: Result):
    logger.debug(f"Creating result: {result}")
    return {"status": "ok"}