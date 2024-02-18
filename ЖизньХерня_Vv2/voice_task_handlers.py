# bot/handlers/voice_task_handlers.py

from aiogram import types
from aiogram.dispatcher import FSMContext
from boty import dp
import schemas
import voice_service
from modelsS import declarative_base as db
from states import VoiceTaskState


@dp.message_handler(content_types=types.ContentTypes.VOICE)
async def handle_voice_task(message: types.Message, state: FSMContext):
    # Отправляем запрос на описание голосовой задачи
    await message.answer("Вы добавили голосовое сообщение. Введите описание:")
    # Устанавливаем состояние, ожидаем ответа с описанием задачи
    await VoiceTaskState.WaitingForDescription.set()
    # Сохраняем идентификатор голосового сообщения в состоянии
    await state.update_data(voice_id=message.voice.file_id)


@dp.message_handler(state=VoiceTaskState.WaitingForDescription)
async def get_voice_task_description(message: types.Message, state: FSMContext):
    # Получаем описание голосовой задачи из сообщения
    description = message.text
    # Получаем идентификатор голосового сообщения из состояния
    data = await state.get_data()
    voice_id = data.get('voice_id')
    # Создаем голосовую задачу и сохраняем в базе данных
    voice_task = schemas.VoiceTaskCreate(description=description, voice_data=voice_id)
    created_task = voice_service.create_voice_task(db, voice_task)
    # Отправляем уведомление об успешном создании задачи
    await message.answer("Голосовая задача успешно добавлена!")
    # Сбрасываем состояние обработчика
    await state.finish()

