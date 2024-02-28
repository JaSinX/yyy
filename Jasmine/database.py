from datetime import datetime
from sqlalchemy.orm import declarative_base
from sqlalchemy import Column, Integer, String, DateTime, Text
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import Enum

Base = declarative_base()

import enum
# учим АНГЛИЙСКИЙ 
# Определение перечисления TaskStatus
class TaskStatus(enum.Enum):
    ACTIVE = 'active' #активный
    COMPLETED = 'completed' #заверщенный
    POSTPONED = 'postponed' #отложено 
    OVERDUE = 'overdue' #просрочено

# Класс модели Task с использованием перечисления TaskStatus
class Task(Base):
    __tablename__ = 'tasks'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer)
    task_text = Column(Text)
    task_type = Column(String)  # тип задачи: text, voice, image
    status = Column(Enum(TaskStatus, name='task_status'))  # статус задачи: active, completed, postponed, overdue
    time = Column(DateTime, default=datetime.utcnow)

# # Создаем подключение к базе данных с помощью асинхронной SQLAlchemy
# engine = create_async_engine("sqlite+aiosqlite:///tasks.db", echo=True)
# async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

# # Функция для создания таблиц в базе данных
# async def create_tables():
#     async with engine.begin() as conn:
#         await conn.run_sync(Base.metadata.create_all)
