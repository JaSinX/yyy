from aiogram.dispatcher.filters.state import State, StatesGroup

from sqlalchemy.ext.asyncio import AsyncSession,create_async_engine
from sqlalchemy.orm import sessionmaker

from database import Base

# Конект бдщкой тип 
engine = create_async_engine("sqlite+aiosqlite:///TOSKA.db", echo=True)
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

# Функция для создания таблиц в базе данных
async def create_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

#МАшина состояний
class States(StatesGroup):
    WAITING_FOR_TASK = State()
    WAITING_FOR_TIME = State()
