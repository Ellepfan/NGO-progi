from fastapi import APIRouter, Depends, status, HTTPException, Request
from sqlalchemy.orm import Session
from sqlalchemy.sql import text
from typing import Annotated
from app.backend.db_depends import get_db
from sqlalchemy import insert, select, update

from app.schemas.result_tasks import Result, CreateResult
from app.schemas.tasks_osb import Tasks, CreateTasks
from slugify import slugify
from datetime import datetime, timedelta

router = APIRouter(
    prefix='/api/result',
    tags=['result'],
)

DbSession = Annotated[Session, Depends(get_db)]


@router.get('/', response_model=list[Result])
async def all_result_task(db: DbSession):
    my_id_res = 0
    select_query = text("SELECT * FROM result WHERE id_res = :id_res")
    result = db.execute(select_query, {"id_res": my_id_res}).fetchall()
    return [Result(id=row.id, task=row.task, data_create_task=row.data_create_task, data_task=row.data_task,
                   flag=row.flag, name_user=row.name_user, data_result_task=row.data_result_task,
                   id_res=row.id_res) for row in result]

@router.get('/monitor', response_model=list[Result])
async def monitor(db: DbSession, request: Request):
    query = text("SELECT * FROM result")
    result = db.execute(query).fetchall()
    return [Result(id=row.id, task=row.task, data_create_task=row.data_create_task, data_task=row.data_task,
                   flag=row.flag, name_user=row.name_user, data_result_task=row.data_result_task,
                   id_res=row.id_res) for row in result]

@router.get('/monitor_good', response_model=list[Result])
async def monitor(db: DbSession, request: Request):
    query = text("SELECT * FROM result")
    result = db.execute(query).fetchall()
    return [Result(id=row.id, task=row.task, data_create_task=row.data_create_task, data_task=row.data_task,
                   flag=row.flag, name_user=row.name_user, data_result_task=row.data_result_task,
                   id_res=row.id_res) for row in result]


@router.get('/result_id_day')
async def result_by_id_day(db: DbSession):
    data_now = str(datetime.now().date())
    data_now = data_now[8:10] + "." + data_now[5:7] + "." + data_now[:4]

    select_query = text("SELECT * FROM result WHERE data_task = :data_task and id_res = 0")
    result = db.execute(select_query, {"data_task": data_now}).fetchall()
    # if not result:
    #
    #     raise HTTPException(status_code=404, detail="Заданий на сегодня нет")
    return [Result(id=row.id, task=row.task, data_create_task=row.data_create_task, data_task=row.data_task,
                   flag=row.flag, name_user=row.name_user, data_result_task=row.data_result_task,
                   id_res=row.id_res) for row in result]


@router.get('/result_id_day_monitor', response_model=list[Result])
async def result_id_day_monitor(db: DbSession):
    # Получаем сегодняшнюю дату в формате YYYY-MM-DD
    today_date = datetime.now().strftime('%Y-%m-%d')

    # Запрос на выборку всех записей, которые не были выполнены сегодня и дата которых уже наступила
    select_query = text("""
        SELECT * FROM result 
        WHERE 
            DATE(SUBSTR(data_task, 7, 4) || '-' || SUBSTR(data_task, 4, 2) || '-' || SUBSTR(data_task, 1, 2)) <= :data_task 
            AND id_res = 0
    """)

    # Выполняем запрос и получаем результаты
    result = db.execute(select_query, {"data_task": today_date}).fetchall()

    # # Если нет результатов, выбрасываем исключение с соответствующим сообщением
    # if not result:
    #     raise HTTPException(status_code=404, detail="Нет заданий, которые не были выполнены и дата которых уже наступила")

    # Возвращаем список результатов в формате Response Model
    return [
        Result(
            id=row.id,
            task=row.task,
            data_create_task=row.data_create_task,
            data_task=row.data_task,
            flag=row.flag,
            name_user=row.name_user,
            data_result_task=row.data_result_task,
            id_res=row.id_res
        ) for row in result
    ]


@router.get('/result_good')
async def result_good(db: DbSession):
    data_now = str(datetime.now().date())
    data_now = data_now[8:10] + "." + data_now[5:7] + "." + data_now[:4]

    select_query = text("SELECT * FROM result WHERE data_result_task = :data_result_task and id_res = 1")
    result = db.execute(select_query, {"data_result_task": data_now}).fetchall()
    # if not result:
    #
    #     raise HTTPException(status_code=404, detail="Заданий на сегодня нет")
    return [Result(id=row.id, task=row.task, data_create_task=row.data_create_task, data_task=row.data_task,
                   flag=row.flag, name_user=row.name_user, data_result_task=row.data_result_task,
                   id_res=row.id_res) for row in result]

@router.get('/result_bad', response_model=list[Result])
async def result_bad(db: DbSession):
    # Получаем сегодняшнюю дату в формате YYYY-MM-DD
    today_date = datetime.now().strftime('%Y-%m-%d')

    # Запрос на выборку всех записей, которые не были выполнены сегодня и дата которых уже наступила
    select_query = text("""
        SELECT * FROM result 
        WHERE 
            DATE(SUBSTR(data_task, 7, 4) || '-' || SUBSTR(data_task, 4, 2) || '-' || SUBSTR(data_task, 1, 2)) < :data_task 
            AND id_res = 0
    """)

    # Выполняем запрос и получаем результаты
    result = db.execute(select_query, {"data_task": today_date}).fetchall()

    # # Если нет результатов, выбрасываем исключение с соответствующим сообщением
    # if not result:
    #     raise HTTPException(status_code=404, detail="Нет заданий, которые не были выполнены и дата которых уже наступила")

    # Возвращаем список результатов в формате Response Model
    return [
        Result(
            id=row.id,
            task=row.task,
            data_create_task=row.data_create_task,
            data_task=row.data_task,
            flag=row.flag,
            name_user=row.name_user,
            data_result_task=row.data_result_task,
            id_res=row.id_res
        ) for row in result
    ]


@router.get('/result_id')
async def result_by_id(result_id: int, db: DbSession):
    select_query = text("SELECT * FROM result WHERE id = :id and id_res = 0")
    result = db.execute(select_query, {"id": result_id}).fetchone()
    if not result:
        raise HTTPException(status_code=404, detail="Task not found")
    return Result(
        id=result.id,
        task=result.task,
        data_create_task=result.data_create_task,
        data_task=result.data_task,
        flag=result.flag,
        name_user=result.name_user,
        data_result_task=result.data_result_task,
        id_res=result.id_res,
    )

@router.put('/update', response_model=Result)
async def update_result(result_id: int , name_user: str, db: DbSession):
    #!!!!!!!!!!!! Выполнение задания!!!!!!!!!!!!!
    data_now = str(datetime.now().date())
    data_now = data_now[8:10] + "." + data_now[5:7] + "." + data_now[:4]
    select_query = text("SELECT * FROM result WHERE id = :id")
    result = db.execute(select_query, {"id": result_id}).fetchone()
    if not result:
        raise HTTPException(status_code=404, detail="Task not found")


    update_query = text(
        "UPDATE result SET flag=:flag, name_user=:name_user, "
        "data_result_task=:data_result_task, id_res=:id_res   "
        "WHERE task = :task and id_res= 0"
    )
    db.execute(
        update_query,
        {
            "id": result.id,
            "task": result.task,
            "data_create_task": result.data_create_task,
            "data_task": result.data_task,
            "flag": "YES",
            "name_user": name_user,
            "data_result_task": data_now,
            "id_res": "1",
        },
    )
#!!!!!!!!!!!!!!!!!!!!!!Создание задания!!!!!!!!!!!!!!!!!!!!!!
    select_query = text("SELECT * FROM tasks WHERE task = :task")
    result_task = db.execute(select_query, {"task": result.task}).fetchone()
    if not result:
        raise HTTPException(status_code=404, detail="Result not found")

    query = text("INSERT INTO result (task, data_create_task, data_task, flag, "
                 "name_user, data_result_task, id_res) VALUES"
                 "(:task, "
                 ":data_create_task, "
                 ":data_task, "
                 ":flag, "
                 ":name_user, "
                 ":data_result_task, "
                 ":id_res)")

    my_day = int(result_task.data_task)
    date_my = datetime.strptime(data_now, '%d.%m.%Y')
    print(date_my)
    result = date_my + timedelta(days=my_day)
    result = str(result)
    my_data_task = result[8:10] + "." + result[5:7] + "." + result[:4]

    db.execute(query, {
        "task": result_task.task,
        "data_create_task": data_now,
        "data_task": my_data_task,
        "flag": "NO",
        "name_user": "NON",
        "data_result_task": "None",
        "id_res": 0
    })
    db.commit()



    # Возвращаем обновлённый продукт
    select_query = text("SELECT * FROM result WHERE task = :task")
    result = db.execute(select_query, {"task": result_task.task}).fetchone()
    return Result(
        id=result.id,
        task=result.task,
        data_create_task=result.data_create_task,
        data_task=result.data_task,
        flag=result.flag,
        name_user=result.name_user,
        data_result_task=result.data_result_task,
        id_res=result.id_res,
    )