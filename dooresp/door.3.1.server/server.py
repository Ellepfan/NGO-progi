from fastapi import FastAPI, HTTPException, Request, Form
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
import uvicorn
import secrets
import os
from datetime import datetime, timedelta
import glob
import time
from typing import Dict, List
import json

app = FastAPI()

# Создаем директории, если их нет
os.makedirs("templates", exist_ok=True)
os.makedirs("logs", exist_ok=True)
os.makedirs("data", exist_ok=True)  # Директория для сохранения данных
os.makedirs("static", exist_ok=True)  # Директория для статических файлов

templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

# Пути к файлам данных
STATE_FILE = "data/server_state.json"
STATS_FILE = "data/server_stats.json"


class LockRequest(BaseModel):
    password: str
    message: str = "Приложение заблокировано администратором"
    target_ip: str = "all"  # "all" или конкретный IP


class UnlockRequest(BaseModel):
    password: str
    target_ip: str = "all"  # "all" или конкретный IP


# Генерация/чтение пароля
try:
    with open("server_secret.txt", "r") as f:
        SERVER_PASSWORD = f.read().strip()
except FileNotFoundError:
    SERVER_PASSWORD = secrets.token_urlsafe(16)
    with open("server_secret.txt", "w") as f:
        f.write(SERVER_PASSWORD)


def load_state():
    """Загружает состояние блокировок из файла"""
    try:
        with open(STATE_FILE, "r") as f:
            data = json.load(f)
            print("Состояние блокировок успешно загружено")
            return data
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Ошибка загрузки состояния: {e}, создано новое")
        return {
            "global_lock": {"is_locked": False, "message": ""},
            "ip_locks": {}
        }


def save_state():
    """Сохраняет текущее состояние блокировок в файл"""
    try:
        with open(STATE_FILE, "w") as f:
            json.dump(lock_state, f, indent=2)
        print("Состояние блокировок сохранено")
    except Exception as e:
        print(f"Ошибка сохранения состояния: {e}")


def load_stats():
    """Загружает статистику из файла"""
    try:
        with open(STATS_FILE, "r") as f:
            data = json.load(f)
            print("Статистика успешно загружена")
            return data
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Ошибка загрузки статистики: {e}, создана новая")
        return {
            "button_presses": 0,
            "client_uptimes": {},
            "ip_activities": {}
        }


def save_stats():
    """Сохраняет текущую статистику в файл"""
    try:
        with open(STATS_FILE, "w") as f:
            json.dump(server_stats, f, indent=2)
        print("Статистика сохранена")
    except Exception as e:
        print(f"Ошибка сохранения статистики: {e}")


# Инициализация состояния и статистики
lock_state = load_state()
server_stats = load_stats()


def log_to_file(message: str):
    log_date = datetime.now().strftime("%Y-%m-%d")
    log_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(f"logs/server_{log_date}.log", "a", encoding="utf-8") as f:
        f.write(f"[{log_time}] {message}\n")


def update_ip_activity(ip: str):
    if ip not in server_stats["ip_activities"]:
        server_stats["ip_activities"][ip] = {
            "last_seen": datetime.now().isoformat(),
            "press_count": 0,
            "is_locked": False
        }
    else:
        server_stats["ip_activities"][ip]["last_seen"] = datetime.now().isoformat()
    save_stats()


@app.get("/api/check_lock")
async def check_lock(request: Request):
    client_ip = request.client.host if request.client else "unknown"
    update_ip_activity(client_ip)

    if lock_state["global_lock"]["is_locked"]:
        log_message = f"Check lock request from {client_ip}. Global lock active."
        log_to_file(log_message)
        return {
            "locked": True,
            "message": lock_state["global_lock"]["message"],
            "is_global": True
        }

    if client_ip in lock_state["ip_locks"] and lock_state["ip_locks"][client_ip]["is_locked"]:
        server_stats["ip_activities"][client_ip]["is_locked"] = True
        log_message = f"Check lock request from {client_ip}. IP lock active."
        log_to_file(log_message)
        return {
            "locked": True,
            "message": lock_state["ip_locks"][client_ip]["message"],
            "is_global": False
        }

    log_message = f"Check lock request from {client_ip}. No active locks."
    log_to_file(log_message)
    return {
        "locked": False,
        "message": "",
        "is_global": False
    }


@app.post("/api/button_press")
async def register_button_press(request: Request):
    client_ip = request.client.host if request.client else "unknown"
    server_stats["button_presses"] += 1
    update_ip_activity(client_ip)

    if client_ip in server_stats["ip_activities"]:
        server_stats["ip_activities"][client_ip]["press_count"] += 1
        save_stats()

    log_message = f"Button pressed from {client_ip}. Total presses: {server_stats['button_presses']}"
    log_to_file(log_message)
    return {"status": "success", "total_presses": server_stats["button_presses"]}


@app.post("/api/client_uptime")
async def register_client_uptime(request: Request, minutes: int):
    client_ip = request.client.host if request.client else "unknown"
    server_stats["client_uptimes"][client_ip] = minutes
    update_ip_activity(client_ip)
    save_stats()
    log_message = f"Client uptime from {client_ip}: {minutes} minutes"
    log_to_file(log_message)
    return {"status": "success"}


@app.get("/api/logs")
async def get_logs(date: str = "today"):
    try:
        logs = []
        if date == "today":
            log_date = datetime.now().strftime("%Y-%m-%d")
            log_file = f"logs/server_{log_date}.log"
            try:
                with open(log_file, "r", encoding="utf-8") as f:
                    logs = [{"timestamp": line.split("]", 1)[0][1:],
                             "message": line.split("]", 1)[1].strip()}
                            for line in f if line.strip()]
            except FileNotFoundError:
                pass
        elif date == "yesterday":
            log_date = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
            log_file = f"logs/server_{log_date}.log"
            try:
                with open(log_file, "r", encoding="utf-8") as f:
                    logs = [{"timestamp": line.split("]", 1)[0][1:],
                             "message": line.split("]", 1)[1].strip()}
                            for line in f if line.strip()]
            except FileNotFoundError:
                pass
        else:
            log_files = sorted(glob.glob("logs/server_*.log"), reverse=True)
            for log_file in log_files:
                try:
                    with open(log_file, "r", encoding="utf-8") as f:
                        logs.extend({"timestamp": line.split("]", 1)[0][1:],
                                     "message": line.split("]", 1)[1].strip()}
                                    for line in f if line.strip())
                except FileNotFoundError:
                    continue

        return JSONResponse(content=logs[-200:])
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/stats")
async def get_stats():
    active_ips = {}
    for ip, data in server_stats["ip_activities"].items():
        active_ips[ip] = {
            "last_seen": data["last_seen"],
            "press_count": data.get("press_count", 0),
            "is_locked": ip in lock_state["ip_locks"] and lock_state["ip_locks"][ip]["is_locked"]
        }
    return {
        "button_presses": server_stats["button_presses"],
        "client_uptimes": server_stats["client_uptimes"],
        "ip_activities": active_ips,
        "global_lock": lock_state["global_lock"]
    }


@app.post("/api/set_lock")
async def set_lock(request: LockRequest):
    if request.password != SERVER_PASSWORD:
        log_to_file("Failed lock attempt: wrong password")
        raise HTTPException(status_code=403, detail="Неверный пароль")

    if request.target_ip.lower() == "all":
        lock_state["global_lock"]["is_locked"] = True
        lock_state["global_lock"]["message"] = request.message
        log_to_file(f"Global lock activated with message: {request.message}")
    else:
        lock_state["ip_locks"][request.target_ip] = {
            "is_locked": True,
            "message": request.message
        }
        if request.target_ip in server_stats["ip_activities"]:
            server_stats["ip_activities"][request.target_ip]["is_locked"] = True
        log_to_file(f"IP lock activated for {request.target_ip} with message: {request.message}")

    save_state()
    save_stats()
    return {"status": "success"}


@app.post("/api/unlock")
async def unlock(request: UnlockRequest):
    if request.password != SERVER_PASSWORD:
        log_to_file("Failed unlock attempt: wrong password")
        raise HTTPException(status_code=403, detail="Неверный пароль")

    if request.target_ip.lower() == "all":
        lock_state["global_lock"]["is_locked"] = False
        lock_state["global_lock"]["message"] = ""
        log_to_file("Global lock deactivated")
    else:
        if request.target_ip in lock_state["ip_locks"]:
            del lock_state["ip_locks"][request.target_ip]
            if request.target_ip in server_stats["ip_activities"]:
                server_stats["ip_activities"][request.target_ip]["is_locked"] = False
            log_to_file(f"IP lock deactivated for {request.target_ip}")

    save_state()
    save_stats()
    return {"status": "success"}


@app.get("/", response_class=HTMLResponse)
async def admin_interface(request: Request):
    stats = await get_stats()
    return templates.TemplateResponse("admin.html", {
        "request": request,
        "global_lock": lock_state["global_lock"],
        "password_set": bool(SERVER_PASSWORD),
        "ip_activities": server_stats["ip_activities"],
        "stats": stats,
        "error": request.query_params.get("error", ""),
        "success": request.query_params.get("success", "")
    })


@app.post("/lock")
async def lock_via_web(password: str = Form(...),
                       message: str = Form(...),
                       target_ip: str = Form(...)):
    if password != SERVER_PASSWORD:
        return RedirectResponse("/?error=Неверный пароль", status_code=303)

    if target_ip.lower() == "all":
        lock_state["global_lock"]["is_locked"] = True
        lock_state["global_lock"]["message"] = message
        log_to_file(f"Web global lock with message: {message}")
    else:
        lock_state["ip_locks"][target_ip] = {
            "is_locked": True,
            "message": message
        }
        if target_ip in server_stats["ip_activities"]:
            server_stats["ip_activities"][target_ip]["is_locked"] = True
        log_to_file(f"Web IP lock for {target_ip} with message: {message}")

    save_state()
    save_stats()
    return RedirectResponse("/?success=Блокировка установлена", status_code=303)


@app.post("/unlock")
async def unlock_via_web(password: str = Form(...),
                         target_ip: str = Form(...)):
    if password != SERVER_PASSWORD:
        return RedirectResponse("/?error=Неверный пароль", status_code=303)

    if target_ip.lower() == "all":
        lock_state["global_lock"]["is_locked"] = False
        lock_state["global_lock"]["message"] = ""
        log_to_file("Web global unlock")
    else:
        if target_ip in lock_state["ip_locks"]:
            del lock_state["ip_locks"][target_ip]
            if target_ip in server_stats["ip_activities"]:
                server_stats["ip_activities"][target_ip]["is_locked"] = False
            log_to_file(f"Web IP unlock for {target_ip}")

    save_state()
    save_stats()
    return RedirectResponse("/?success=Блокировка снята", status_code=303)


if __name__ == "__main__":
    print(f"Сервер запущен. Пароль: {SERVER_PASSWORD}")
    print(f"Веб-интерфейс: http://127.0.0.1:8000")
    log_to_file("Server started")
    uvicorn.run(app, host="0.0.0.0", port=8000)