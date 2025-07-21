from fastapi import FastAPI, Body , HTTPException, WebSocket
from app.backend.db import engine, Base
from app.routers import result_tasks, tasks_osb
from app.pages.router import router as router_pages
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from fastapi.staticfiles import StaticFiles
from typing import List

app = FastAPI(swagger_ui_parameters={"tryItOutEnabled": True}, debug=True)

templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")
app.include_router(result_tasks.router)
app.include_router(tasks_osb.router)

Base.metadata.create_all(bind=engine)

app.include_router(router_pages)
@app.get("/")
async def Welcome():
    return {"message": "Welcome to Taskmanager"}

class Result(BaseModel):
    id: int
    name_user: str

# Хранение подключенных клиентов
clients: List[WebSocket] = []































