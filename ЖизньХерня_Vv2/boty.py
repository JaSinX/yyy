# bot.py

from aiogram import Bot, Dispatcher, types
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.utils import executor
from aiogram.contrib.fsm_storage.memory import MemoryStorage
TOKEN = "6323031981:AAG-Q8HsZG92b8D-yMA0Okcbwi7JN_29Oho"

# Создание экземпляра бота
bot = Bot(token=TOKEN)

# Создание экземпляра диспетчера

storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)
# Добавление логгирования
dp.middleware.setup(LoggingMiddleware())

# Ваши обработчики здесь

# Функция для запуска бота
def run():
    executor.start_polling(dp, skip_updates=True)
