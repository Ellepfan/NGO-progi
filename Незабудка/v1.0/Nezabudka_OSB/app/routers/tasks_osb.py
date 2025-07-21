from fastapi import APIRouter, Depends, status, HTTPException, Request
from sqlalchemy.orm import Session
from sqlalchemy.sql import text
from typing import Annotated
from app.backend.db_depends import get_db
from sqlalchemy import insert, select, update
from app.schemas.tasks_osb import Tasks, CreateTasks
from app.schemas.result_tasks import Result, CreateResult
from slugify import slugify
from datetime import datetime, timedelta


router = APIRouter(prefix='/api/tasks', tags=['tasks'])


DbSession = Annotated[Session, Depends(get_db)]


@router.get('/', response_model=list[Tasks])
async def all_task(db: DbSession, request: Request):
    query = text("SELECT * FROM tasks")
    result = db.execute(query).fetchall()
    return [Tasks(id=row.id, task=row.task, data_create_task=row.data_create_task, data_task=row.data_task,
                  onoff=row.onoff) for row in result]


@router.get('/task')
async def task_by_id(id_task: int, db: DbSession):
    select_query = text("SELECT * FROM tasks WHERE id = :id")
    result = db.execute(select_query, {"id": id_task}).fetchone()
    if not result:
        raise HTTPException(status_code=404, detail="Task not found")
    return Tasks(
        id=result.id,
        task=result.task,
        data_create_task=result.data_create_task,
        data_task=result.data_task,
        onoff=result.onoff)


@router.get('/task_all_one')
async def task_all_one(task_all: str, db: DbSession):
    select_query = text("SELECT * FROM result WHERE task = :task")
    result = db.execute(select_query, {"task": task_all}).fetchall()
    if not result:
        raise HTTPException(status_code=404, detail="Task not found")
    return [Result(id=row.id, task=row.task, data_create_task=row.data_create_task, data_task=row.data_task,
                   flag=row.flag, name_user=row.name_user, data_result_task=row.data_result_task,
                   id_res=row.id_res) for row in result]


@router.post('/create', response_model=Tasks)
async def create_task(task: CreateTasks, db: DbSession):
    query = text("INSERT INTO tasks (task, data_create_task, data_task, onoff) VALUES"
                 "(:task, "
                 ":data_create_task, "
                 ":data_task, "
                 ":onoff)")

    current_date = datetime.today()
    my_day = int(task.data_task)
    my_str = '09-24-2023'  # 👉️ (mm-dd-yyyy)
    date_my = datetime.strptime(task.data_create_task, '%d.%m.%Y')
    result = date_my + timedelta(days=my_day)
    result = str(result)
    my_data_task = result[8:10] + "." + result[5:7] + "." + result[:4]

    db.execute(query, {
        "task": task.task,
        "data_create_task": task.data_create_task,
        "data_task": task.data_task,
        "onoff": "ON"})
    db.commit()

    query = text("INSERT INTO result (task, data_create_task, data_task, flag, "
                 "name_user, data_result_task, id_res) VALUES"
                 "(:task, "
                 ":data_create_task, "
                 ":data_task, "
                 ":flag, "
                 ":name_user, "
                 ":data_result_task, "
                 ":id_res)")

    db.execute(query, {
        "task": task.task,
        "data_create_task": task.data_create_task,
        "data_task": my_data_task,
        "flag": "NO",
        "name_user": "Non",
        "data_result_task": "NONE",
        "id_res": 0
    })
    db.commit()

    select_query = text("SELECT * FROM tasks WHERE task = :task")
    result = db.execute(select_query, {"task": task.task}).fetchone()
    return Tasks(
        id=result.id,
        task=result.task,
        data_create_task=result.data_create_task,
        data_task=result.data_task,
        onoff=result.onoff
    )


@router.put('/update_OFF', response_model=Tasks)
async def task_OFF(my_task: str, db: DbSession):
    select_query = text("SELECT * FROM tasks WHERE task = :task")
    result_t = db.execute(select_query, {"task": my_task}).fetchone()
    if not result_t:
        raise HTTPException(status_code=404, detail="Task not found")
    update_query = text(
        "UPDATE tasks SET id = :id, data_create_task= :data_create_task, "
        "data_task= :data_task, onoff= :onoff WHERE task= :task"
    )
    db.execute(
        update_query,
        {
            "id": result_t.id,
            "task": result_t.task,
            "data_create_task": "NONE",
            "data_task": result_t.data_task,
            "onoff": "OFF"
        },
    )
    db.commit()
    select_query = text("SELECT * FROM result WHERE task = :task")
    result = db.execute(select_query, {"task": my_task}).fetchone()
    if not result:
        raise HTTPException(status_code=404, detail="Task not found")

    update_query = text(
        "UPDATE result SET flag=:flag, name_user=:name_user, "
        "data_result_task=:data_result_task, id_res=:id_res "
        "WHERE task = :task and id_res = 0"
    )

    db.execute(
        update_query,
        {
            "task": result.task,
            "data_create_task": "OFF",
            "data_task": result.data_task,
            "flag": "OFF",
            "name_user": "OFF",
            "data_result_task": "OFF",
            "id_res": 3
        },
    )
    db.commit()
    # Возвращаем обновлённый продукт
    select_query = text("SELECT * FROM tasks WHERE task = :task")
    updated_result = db.execute(select_query, {"task": my_task}).fetchone()
    return Tasks(
        id=updated_result.id,
        task=updated_result.task,
        data_create_task=updated_result.data_create_task,
        data_task=updated_result.data_task,
        onoff=updated_result.onoff,
    )


@router.put('/update_ON', response_model=Tasks)
async def task_on(my_task: str, my_data_create_task: str, my_data_task: int, db: DbSession):
    select_query = text("SELECT * FROM tasks WHERE task = :task")
    result = db.execute(select_query, {"task": my_task}).fetchone()
    if not result:
        raise HTTPException(status_code=404, detail="Task not found")
    update_query = text(
        "UPDATE tasks SET id = :id, data_create_task= :data_create_task, "
        "data_task= :data_task, onoff= :onoff WHERE task= :task"
    )

    db.execute(
        update_query,
        {
            "id": result.id,
            "task": result.task,
            "data_create_task": my_data_create_task,
            "data_task": my_data_task,
            "onoff": "ON"
        },
    )
    db.commit()

    select_query = text("SELECT * FROM result WHERE task = :task")
    result_r = db.execute(select_query, {"task": my_task}).fetchone()
    if not result:
        raise HTTPException(status_code=404, detail="Task not found")

    update_query = text(
        "UPDATE result SET flag=:flag, name_user=:name_user, "
        "data_result_task=:data_result_task, data_task=:data_task, id_res=:id_res WHERE task = :task and id_res= 3 "
    )

    my_day = int(my_data_task)
    # my_str = '09-24-2023'  # 👉️ (mm-dd-yyyy)
    date_my = datetime.strptime(my_data_create_task, '%d.%m.%Y')
    result1 = date_my + timedelta(days=my_day)
    result1 = str(result1)
    my_data_task = result1[8:10] + "." + result1[5:7] + "." + result1[:4]
    db.execute(
        update_query,
        {
            "task": result_r.task,
            "data_create_task": my_data_create_task,
            "data_task": my_data_task,
            "flag": "NO",
            "name_user": "Non",
            "data_result_task": "None",
            "id_res": 0
        },
    )
    db.commit()

    # Возвращаем обновлённый продукт
    select_query = text("SELECT * FROM tasks WHERE task = :task")
    updated_result = db.execute(select_query, {"task": my_task}).fetchone()
    return Tasks(
        id=updated_result.id,
        task=updated_result.task,
        data_create_task=updated_result.data_create_task,
        data_task=updated_result.data_task,
        onoff=updated_result.onoff
    )
#
# @router.delete('/delete/{category_id}')
# async def delete_task(task_id: int, db: DbSession):
#     select_query = text("SELECT * FROM tasks WHERE id = :id")
#     result = db.execute(select_query, {"id": task_id}).fetchone()
#     if not result:
#         raise HTTPException(status_code=404, detail="Task not found")
#     delete_query = text("DELETE FROM tasks WHERE id = :id")
#     db.execute(delete_query, {"id": task_id})
#     db.commit()
#     return {"message": "Task deleted"}
