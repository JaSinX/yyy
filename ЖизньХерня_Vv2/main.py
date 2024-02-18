# main.py

# from aiogram import executor
# from bot import dp, setup

# async def on_startup(dispatcher):
#     await setup(dispatcher.bot)

# if __name__ == "__main__":
#     from bot import dp
#     from bot.handlers import *
#     from bot.middlewares import setup_middlewares

#     # Инициализация мидлваров
#     setup_middlewares(dp)

#     # Добавление обработчиков
#     executor.start_polling(dp, on_startup=on_startup)
# _________________________________________
from boty import dp



from aiogram import Bot, Dispatcher, types
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.utils import executor
# Регистрация обработчиков команд и сообщений
async def on_startup(dp):
    from photo_service import create_photo_task,update_photo_task,get_photo_task_by_id,delete_photo_task
    from task_executor import execute_image_task,execute_task,execute_text_task,execute_voice_task

    from task_service import get_text_task_by_id,get_all_text_tasks,delete_text_task,create_text_task,update_text_task
    from photo_task_handlers import get_photo_task_description,handle_photo_task
    from voice_service import delete_voice_task,create_voice_task,update_voice_task,get_voice_task_by_id
    from voice_task_handlers import get_voice_task_description,handle_voice_task
    # Другие обработчики здесь
    # Инициализация мидлваров
    from task_handlers import add_task,handle_text_task
if __name__ == "__main__":

    dp.middleware.setup(LoggingMiddleware())


    # Инициализация мидлваров


    # Добавление обработчиков
    executor.start_polling(dp,on_startup=on_startup)





