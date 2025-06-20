from pydantic import BaseModel


class TasksBase(BaseModel):
    id: int
    task: str
    data_create_task: str
    data_task: str
    onoff: str


class CreateTasks(TasksBase):
    pass

class Tasks(TasksBase):
    id: int


class Config:
    orm_mode = True  # Позволяет работать с данными ORM