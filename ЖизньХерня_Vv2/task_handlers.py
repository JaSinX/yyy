# bot/handlers/task_handlers.py

from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.types import CallbackQuery
from aiogram.types.inline_keyboard import InlineKeyboardButton, InlineKeyboardMarkup
from boty import dp
from modelsS import TextTask, VoiceTask, PhotoTask
import task_service
from modelsS import declarative_base as db
import schemas
from modelsS import SessionLocal
from states import TextTaskState

# Общий обработчик для всех типов задач
@dp.message_handler(commands=['add_task'])
async def add_task(message: types.Message, state: FSMContext):
    # Отправляем сообщение пользователю с запросом на ввод текста задачи
    await message.answer("Введите текст задачи:")
    # Переходим в состояние ожидания ввода текста задачи
    await state.set_state('wait_task_text')

@dp.message_handler(content_types=types.ContentTypes.TEXT, state='wait_task_text')
async def handle_text_task(message: types.Message, state: FSMContext):
    # Получаем текст сообщения
    text = message.text
    # Создаем объект с информацией о текстовой задаче
    text_task_data = schemas.TextTaskCreate(description=text)
    # Создаем текстовую задачу в базе данных
    session = SessionLocal()
    created_task = task_service.create_text_task(session, text_task_data)

    # Отправляем уведомление об успешном создании задачи
    await message.answer("Текстовая задача успешно добавлена!")
    # Сбрасываем состояние FSMContext
    await state.finish()



