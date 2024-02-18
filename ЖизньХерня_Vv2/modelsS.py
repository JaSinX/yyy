# bot/models/models.py


import enum

class TaskStatus(enum.Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    POSTPONED = "postponed"
    SKIPPED = "skipped"

from sqlalchemy import Column, Integer, String, Enum, DateTime
from sqlalchemy.orm import declarative_base


Base = declarative_base()

# Модель задачи
class Task(Base):
    __tablename__ = "tasks"
    id = Column(Integer, primary_key=True, index=True)
    description = Column(String, index=True)
    status = Column(Enum(TaskStatus), default=TaskStatus.PENDING)
    created_at = Column(DateTime)

# Здесь также могут быть определены модели для текстовых, фото- и голосовых задач
# Например:
class TextTask(Base):
    __tablename__ = "text_tasks"
    id = Column(Integer, primary_key=True, index=True)
    description = Column(String, index=True)
    status = Column(Enum(TaskStatus), default=TaskStatus.PENDING)
    created_at = Column(DateTime)

class PhotoTask(Base):
    __tablename__ = "photo_tasks"
    id = Column(Integer, primary_key=True, index=True)
    file_path = Column(String, index=True)
    status = Column(Enum(TaskStatus), default=TaskStatus.PENDING)
    created_at = Column(DateTime)

class VoiceTask(Base):
    __tablename__ = "voice_tasks"
    id = Column(Integer, primary_key=True, index=True)
    file_path = Column(String, index=True)
    status = Column(Enum(TaskStatus), default=TaskStatus.PENDING)
    created_at = Column(DateTime)

from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine

# Создаем соединение с базой данных
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL)

# Создаем фабрику сессий
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Теперь вы можете создавать объекты сессии, используя SessionLocal()
session = SessionLocal()

# Используйте этот объект сессии для выполнения запросов к базе данных
