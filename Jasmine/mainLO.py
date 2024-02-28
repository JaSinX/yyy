from datetime import datetime
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select, and_, or_

import pytz
from aiogram.types import ContentType
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
import logging
import asyncio
from datetime import timedelta
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from database import Task,TaskStatus, Base
from aiogram.contrib.fsm_storage.memory import MemoryStorage

# Создаем подключение к базе данных
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine

API = "6323031981:AAG-Q8HsZG92b8D-yMA0Okcbwi7JN_29Oho"
bot = Bot(token=API)
storage = MemoryStorage()
# Создаем диспетчер с указанием хранилища
dp = Dispatcher(bot, storage=storage)
dp.middleware.setup(LoggingMiddleware())


# Создаем подключение к базе данных с помощью асинхронной SQLAlchemy
engine = create_async_engine("sqlite+aiosqlite:///tasks.db", echo=True)
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

# Функция для создания таблиц в базе данных
async def create_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


# Состояния бота
class States(StatesGroup):
    WAITING_FOR_TASK = State()
    WAITING_FOR_TIME = State()

# Обработчик кнопки для добавления задачи
@dp.message_handler(commands=['start'])
async def start_command(message: types.Message):
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(types.KeyboardButton(text="Добавить задачу"))
    await message.answer("Привет! Чем могу помочь?", reply_markup=keyboard)

@dp.message_handler(lambda message: message.text == "Добавить задачу")
async def add_task(message: types.Message):
    await message.answer("Отправьте мне вашу задачу в формате текста, голосового сообщения или изображения.")
    await States.WAITING_FOR_TASK.set()

# Обработчик текстовых сообщений
@dp.message_handler(content_types=ContentType.TEXT, state=States.WAITING_FOR_TASK)
async def handle_text(message: types.Message, state: FSMContext):
    await state.update_data(user_id=message.from_user.id, task_text=message.text, task_type="text")
    await message.answer("Отправьте время в формате HH:MM")
    await States.WAITING_FOR_TIME.set()  # Переходим в состояние ожидания времени

# Обработчик голосовых сообщений
@dp.message_handler(content_types=ContentType.VOICE, state=States.WAITING_FOR_TASK)
async def handle_voice(message: types.Message, state: FSMContext):
    await state.update_data(user_id=message.from_user.id, task_text=message.voice.file_id, task_type="voice")
    await message.answer("Отправьте время в формате HH:MM")
    await States.WAITING_FOR_TIME.set()  # Переходим в состояние ожидания времени

# Обработчик изображений
@dp.message_handler(content_types=ContentType.PHOTO, state=States.WAITING_FOR_TASK)
async def handle_photo(message: types.Message, state: FSMContext):
    await state.update_data(user_id=message.from_user.id, task_text=message.photo[-1].file_id, task_type="image")
    await message.answer("Отправьте время в формате HH:MM")
    await States.WAITING_FOR_TIME.set()  # Переходим в состояние ожидания времени

# Обработчик ввода времени
@dp.message_handler(content_types=ContentType.TEXT, state=States.WAITING_FOR_TIME)
async def handle_time_input(message: types.Message, state: FSMContext):
    time_str = message.text
    try:
        # Получаем текущее время в UTC
        current_time_utc = datetime.now(pytz.utc)

        # Преобразуем время задачи в UTC
        user_timezone = pytz.timezone('Europe/Moscow')  # Замените на часовой пояс пользователя
        time_obj = datetime.strptime(time_str, "%H:%M")
        time_obj = time_obj.replace(year=current_time_utc.year, month=current_time_utc.month, day=current_time_utc.day)
        time_obj = user_timezone.localize(time_obj)
        time_obj_utc = time_obj.astimezone(pytz.utc)

        # Если время задачи меньше текущего времени, добавляем один день
        if time_obj_utc <= current_time_utc:
            time_obj_utc += timedelta(days=1)

        user_data = await state.get_data()
        user_id = user_data.get('user_id')
        task_text = user_data.get('task_text')
        task_type = user_data.get('task_type')
        async with async_session() as session:
            # new_task = Task(user_id=user_id, task_text=task_text, task_type=task_type, status=TaskStatus.ACTIVE.value, time=time_obj_utc)

            new_task = Task(user_id=user_id, task_text=task_text, task_type=task_type, status=TaskStatus.ACTIVE, time=time_obj_utc)
            session.add(new_task)
            await session.commit()
            await bot.send_message(user_id, "Задача добавлена и будет выполнена в указанное время.")
            await state.finish()  # Завершаем состояние после успешного добавления задачи
            await send_reminder(session, new_task)
    except ValueError:
        await message.answer("Неверный формат времени. Попробуйте снова.")
from datetime import datetime
import pytz

# Получаем текущее время в UTC с информацией о временной зоне

async def check_tasks():
    while True:
        async with async_session() as session:
            current_time_utc = datetime.now(pytz.utc)

            # Получаем все активные задачи, учитывая возможные изменения времени задачи
            tasks = await session.execute(
                select(Task).where(
                    and_(
                        or_(
                            Task.status == TaskStatus.ACTIVE,
                            Task.status == TaskStatus.POSTPONED
                        ),
                        
                        
                        Task.time <= current_time_utc + timedelta(minutes=1)  # Увеличиваем на 1 минуту для учета погрешности
                    )
                )
            )
            for task in tasks.scalars():
                task_time_utc = task.time.replace(tzinfo=pytz.UTC)
                if task_time_utc <= current_time_utc:
                    print("Найдена активная задача:", task.id, task.user_id, task.task_text, task.task_type, task.status, task.time)
                    # Проверяем, что задача не завершена и не пропущена, прежде чем вызывать функцию для обработки уведомления
                    if task.status not in [TaskStatus.COMPLETED, TaskStatus.OVERDUE]:  
                        await handle_expired_task(session, task)

        await asyncio.sleep(60)  # Проверяем задачи каждую минуту



async def send_reminder(session, task):
    try:
        current_time_utc = datetime.now(pytz.utc)

        # Преобразуем время задачи к формату с информацией о временной зоне (UTC)
        task_time_utc = task.time.replace(tzinfo=pytz.utc)

        if task_time_utc <= current_time_utc and task.status != TaskStatus.OVERDUE:
            # Создаем инлайн клавиатуру с тремя кнопками: Завершить, Отложить и Пропустить
            inline_keyboard = types.InlineKeyboardMarkup()
            inline_keyboard.add(
                types.InlineKeyboardButton(text="Завершить", callback_data=f"complete_task:{task.id}"),
                types.InlineKeyboardButton(text="Отложить", callback_data=f"delay_task:{task.id}"),
                types.InlineKeyboardButton(text="Пропустить", callback_data=f"skip_task:{task.id}")
            )

            if task.task_type == "text":
                await bot.send_message(task.user_id, f"Напоминание: {task.task_text}", reply_markup=inline_keyboard)
            elif task.task_type == "voice":
                await bot.send_voice(task.user_id, task.task_text, reply_markup=inline_keyboard)
            elif task.task_type == "image":
                await bot.send_photo(task.user_id, task.task_text, reply_markup=inline_keyboard)

    except Exception as e:
        logging.exception("Ошибка при отправке уведомления: %s", e)


# Обработчик нажатия кнопки "Завершить"
@dp.callback_query_handler(lambda callback_query: callback_query.data.startswith('complete_task'))
async def complete_task(callback_query: types.CallbackQuery):
    task_id = int(callback_query.data.split(':')[1])  # Получаем идентификатор задачи из callback_data
    async with async_session() as session:
        task = await session.get(Task, task_id)
        if task:
            task.status = TaskStatus.COMPLETED
            await session.commit()
            await bot.answer_callback_query(callback_query.id, "Задача завершена")
        else:
            await bot.answer_callback_query(callback_query.id, "Задача не найдена")

# Обработчик нажатия кнопки "Отложить"
@dp.callback_query_handler(lambda callback_query: callback_query.data.startswith('delay_task'))
async def delay_task(callback_query: types.CallbackQuery, state: FSMContext):
    task_id = int(callback_query.data.split(':')[1])  # Получаем идентификатор задачи из callback_data

    # Создаем клавиатуру с кнопками выбора интервала времени
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(
        types.InlineKeyboardButton(text="Отложить на 1 минуту", callback_data=f"confirm_delay:{task_id}:1"),
        types.InlineKeyboardButton(text="Отложить на 3 минуты", callback_data=f"confirm_delay:{task_id}:3")
    )

    # Изменяем статус задачи на "Отложенный" в базе данных
    async with async_session() as session:
        task = await session.get(Task, task_id)
        if task:
            task.status = TaskStatus.POSTPONED
            await session.commit()

    await bot.edit_message_reply_markup(callback_query.message.chat.id, callback_query.message.message_id, reply_markup=keyboard)

# Обработчик выбора временного интервала для отложенного уведомления
@dp.callback_query_handler(lambda callback_query: callback_query.data.startswith('confirm_delay'))
async def confirm_delay(callback_query: types.CallbackQuery):
    task_id, delay_minutes = map(int, callback_query.data.split(':')[1:])
    async with async_session() as session:
        task = await session.get(Task, task_id)
        if task:
            # Применяем выбранный интервал времени к времени задачи
            task.time += timedelta(minutes=delay_minutes)
            await session.commit()
            await bot.answer_callback_query(callback_query.id, f"Задача отложена на {delay_minutes} минут")
            
            # Запускаем асинхронную задачу, которая будет ждать указанное количество минут
            await asyncio.sleep(delay_minutes * 60)
            
            # После ожидания отправляем уведомление о задаче
            try:
                if task.task_type == "text":
                    await bot.send_message(task.user_id, f"Напоминание: {task.task_text}")
                elif task.task_type == "voice":
                    await bot.send_voice(task.user_id, task.task_text)
                elif task.task_type == "image":
                    await bot.send_photo(task.user_id, task.task_text)
            except Exception as e:
                logging.exception("Ошибка при отправке уведомления: %s", e)
        else:
            await bot.answer_callback_query(callback_query.id, "Задача не найдена")

async def handle_expired_task(session, task):
    try:
        if task.status not in [TaskStatus.COMPLETED, TaskStatus.OVERDUE]:  # Проверяем, что статус не "COMPLETED" и не "OVERDUE"
            current_time_utc = datetime.utcnow().replace(tzinfo=None)  # Получаем текущее время в UTC в формате naive datetime
            task_time_utc = task.time.replace(tzinfo=None)  # Приводим время задачи к naive datetime
            if task_time_utc <= current_time_utc:
                # Отправляем уведомление о задаче
                if task.task_type == "text":
                    await bot.send_message(task.user_id, f"Напоминание: {task.task_text}")
                elif task.task_type == "voice":
                    await bot.send_voice(task.user_id, task.task_text)
                elif task.task_type == "image":
                    await bot.send_photo(task.user_id, task.task_text)
                    
                # После отправки уведомления предлагаем пользователю выбрать действие
                inline_keyboard = types.InlineKeyboardMarkup()
                inline_keyboard.add(
                    types.InlineKeyboardButton(text="Завершено", callback_data=f"complete_task:{task.id}"),
                    types.InlineKeyboardButton(text="Отложить", callback_data=f"delay_task:{task.id}"),
                    types.InlineKeyboardButton(text="Пропустить", callback_data=f"skip_task:{task.id}")
                )
                await bot.send_message(task.user_id, "Что вы хотите сделать с этой задачей?", reply_markup=inline_keyboard)
    except Exception as e:
        logging.exception("Ошибка при отправке уведомления: %s", e)



# Обработчик нажатия кнопки "Пропустить"
@dp.callback_query_handler(lambda callback_query: callback_query.data.startswith('skip_task'))
async def skip_task(callback_query: types.CallbackQuery):
    task_id = int(callback_query.data.split(':')[1])  # Получаем идентификатор задачи из callback_data
    async with async_session() as session:
        task = await session.get(Task, task_id)
        if task:
            task.status = TaskStatus.OVERDUE 
            await session.commit()
            await bot.answer_callback_query(callback_query.id, "Задача пропущена")
        else:
            await bot.answer_callback_query(callback_query.id, "Задача не найдена")


async def check_tasks_periodically():
    while True:
        await asyncio.sleep(60)  # Ждем 60 секунд перед следующей проверкой
        await check_tasks()

from  aiogram.utils import executor


async def main():
    await create_tables()
    dp.register_message_handler(start_command, commands=['start'])
    dp.register_message_handler(add_task, lambda message: message.text == "Добавить задачу")
    dp.register_message_handler(handle_text, content_types=ContentType.TEXT, state=States.WAITING_FOR_TASK)
    dp.register_message_handler(handle_voice, content_types=ContentType.VOICE, state=States.WAITING_FOR_TASK)
    dp.register_message_handler(handle_photo, content_types=ContentType.PHOTO, state=States.WAITING_FOR_TASK)
    dp.register_message_handler(handle_time_input, content_types=ContentType.TEXT, state=States.WAITING_FOR_TIME)
    asyncio.create_task(check_tasks_periodically())  # Запускаем периодическую проверку задач

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.create_task(main())
    executor.start_polling(dp, skip_updates=True)