from app.backend.db import Base
from sqlalchemy import Column, ForeignKey, Integer, String, Boolean
from sqlalchemy.orm import relationship


class Task(Base):
    __tablename__ = 'tasks'
    id = Column(Integer, primary_key=True, index=True)
    task = Column(String, unique=True, index=True)
    data_create_task = Column(String, index=True)
    data_task = Column(String, index=True)
    onoff = Column(String, index=True)
    result = relationship('Task', back_populates='result')


from sqlalchemy.schema import CreateTable

print(CreateTable(Task.__table__))
