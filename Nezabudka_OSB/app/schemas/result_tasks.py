from pydantic import BaseModel


class ResultBase(BaseModel):
    id: int
    task: str
    flag: str
    name_user: str
    data_create_task: str
    data_task: str
    data_result_task: str
    id_res: int

class CreateResult(ResultBase):
    pass

class Result(ResultBase):
    id: int


class Config:
    orm_mode = True  # Позволяет работать с данными ORM