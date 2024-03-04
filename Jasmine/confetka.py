
import asyncio

from aiogram.utils import executor
from aiogram import Bot, Dispatcher
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.contrib.middlewares.logging import LoggingMiddleware



API = "6323031981:AAG-Q8HsZG92b8D-yMA0Okcbwi7JN_29Oho"
bot = Bot(token=API)
storage = MemoryStorage()
# временое хранилице
dp = Dispatcher(bot, storage=storage)
dp.middleware.setup(LoggingMiddleware())


