from app.backend.db import Base
from sqlalchemy import Column, ForeignKey, Integer, String, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.schema import CreateTable


class Result(Base):
    __tablename__ = 'result'

    id = Column(Integer, primary_key=True, index=True)
    task = Column(String, ForeignKey('tasks.task'), index=True, nullable=False)
    data_create_task = Column(String, index=True)
    data_task = Column(String, index=True)
    flag = Column(String, index=True)
    name_user = Column(String, index=True)
    data_result_task = Column(String, index=True)
    id_res = Column(Integer, index=True)




print(CreateTable(Result.__table__))