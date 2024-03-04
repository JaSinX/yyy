import enum

from datetime import datetime

from sqlalchemy import Column, Integer, String, DateTime, Text,Enum
from sqlalchemy.orm import declarative_base


Base = declarative_base()


# учим АНГЛИЙСКИЙ 
# Определение перечисления TaskStatus
class TaskStatus(enum.Enum):
    ACTIVE = 'active' #активный
    COMPLETED = 'completed' #заверщенный
    POSTPONED = 'postponed' #отложено 
    OVERDUE = 'overdue' #просрочено

# Класс модели Task с TaskStatus
class Task(Base):
    __tablename__ = 'tasks'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer)
    task_text = Column(Text)
    task_type = Column(String)  # тип тип text, voice, image
    status = Column(Enum(TaskStatus, name='task_status'))  # статус задачи
    time = Column(DateTime, default=datetime.utcnow)


