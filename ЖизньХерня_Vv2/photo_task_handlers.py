# bot/handlers/photo_handlers.py

from aiogram import types
from aiogram.dispatcher import FSMContext

import schemas
import photo_service
from modelsS import declarative_base as db
from states import PhotoTaskState
from boty import dp

@dp.message_handler(content_types=types.ContentTypes.PHOTO)
async def handle_photo_task(message: types.Message, state: FSMContext):
    # Получаем идентификатор фото из сообщения
    photo_id = message.photo[-1].file_id
    # Отправляем запрос на описание фото-задачи
    await message.answer("Вы добавили фото. Введите описание:")
    # Устанавливаем состояние, ожидаем ответа с описанием задачи
    await PhotoTaskState.WaitingForDescription.set()
    # Сохраняем идентификатор фото в состоянии
    await state.update_data(photo_id=photo_id)


@dp.message_handler(state=PhotoTaskState.WaitingForDescription)
async def get_photo_task_description(message: types.Message, state: FSMContext):
    # Получаем описание фото-задачи из сообщения
    description = message.text
    # Получаем идентификатор фото из состояния
    data = await state.get_data()
    photo_id = data.get('photo_id')
    # Создаем фото-задачу и сохраняем в базе данных
    photo_task = schemas.PhotoTaskCreate(description=description, image_data=photo_id)
    created_task = photo_service.create_photo_task(db, photo_task)
    # Отправляем уведомление об успешном создании задачи
    await message.answer("Фото-задача успешно добавлена!")
    # Сбрасываем состояние обработчика
    await state.finish()
