from datetime import datetime
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select, and_, or_,func


import pytz
from aiogram.types import ContentType
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text
from aiogram.dispatcher.filters.state import State, StatesGroup
import logging
import asyncio
from datetime import timedelta
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from database import Task,TaskStatus, Base
from aiogram.contrib.fsm_storage.memory import MemoryStorage

# from main import list_tasks_command,help_command,clean_chat_command

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine

API = "6323031981:AAG-Q8HsZG92b8D-yMA0Okcbwi7JN_29Oho"
bot = Bot(token=API)
storage = MemoryStorage()
# временое хранилице
dp = Dispatcher(bot, storage=storage)
dp.middleware.setup(LoggingMiddleware())


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

# Стартик
@dp.message_handler(commands=['start'])
async def start_command(message: types.Message):
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(types.KeyboardButton(text="Добавить задачу"))
    await message.answer("Добро пожаловать дорогой пользователь!\nЭто бот ChronoEvent,ты можешь отправить мне задачи, а я буду напоминать о них тебе.\n Чем могу помочь?", reply_markup=keyboard)
                                                    #тут добавть нужно имя юзера 

@dp.message_handler(Text(equals="отмена", ignore_case=True), state="*") 
async def cancel_handler(message: types.Message, state: FSMContext):
    current_state = await state.get_state() 
    if current_state is None:
        return
    await state.finish()
    await message.reply("""Хорошо вы прервали текущий процесс. Если хотите добавить задачу, нажмите на\n\
"Добавить задачу". Если нужна помощь, то введите "/help".""")


@dp.message_handler(lambda message: message.text == "Добавить задачу")
async def add_task(message: types.Message):
    await message.answer("Отправьте мне вашу задачу в формате текста, голосового сообщения или изображения.")
    await States.WAITING_FOR_TASK.set()


# Хендлер текстовых сообщений
@dp.message_handler(content_types=ContentType.TEXT, state=States.WAITING_FOR_TASK)
async def handle_text(message: types.Message, state: FSMContext):
    await state.update_data(user_id=message.from_user.id, task_text=message.text, task_type="text")
    await message.answer("Отправьте время в формате HH:MM")
    await States.WAITING_FOR_TIME.set()  # Переходим в состояние ожидания времени

# Хендлер голосовых сообщений
@dp.message_handler(content_types=ContentType.VOICE, state=States.WAITING_FOR_TASK)
async def handle_voice(message: types.Message, state: FSMContext):
    await state.update_data(user_id=message.from_user.id, task_text=message.voice.file_id, task_type="voice")
    await message.answer("Отправьте время в формате HH:MM")
    await States.WAITING_FOR_TIME.set()  # Переходим в состояние ожидания времени

# Хендлер изображений
@dp.message_handler(content_types=ContentType.PHOTO, state=States.WAITING_FOR_TASK)
async def handle_photo(message: types.Message, state: FSMContext):
    await state.update_data(user_id=message.from_user.id, task_text=message.photo[-1].file_id, task_type="image")
    await message.answer("Отправьте время в формате HH:MM")
    await States.WAITING_FOR_TIME.set()  # Переходим в состояние ожидания времени

# Хендлер ввода времени в формате ЧЧ:ММ
@dp.message_handler(content_types=ContentType.TEXT, state=States.WAITING_FOR_TIME)
async def handle_time_input(message: types.Message, state: FSMContext):
    time_str = message.text
    try:
        #текущее время в UTC
        current_time_utc = datetime.now(pytz.utc)

        # Преобразуем время задачи в UTC
        user_timezone = pytz.timezone('Europe/Moscow')  
        time_obj = datetime.strptime(time_str, "%H:%M")
        time_obj = time_obj.replace(year=current_time_utc.year, month=current_time_utc.month, day=current_time_utc.day)
        time_obj = user_timezone.localize(time_obj)
        time_obj_utc = time_obj.astimezone(pytz.utc)

        # Если время задачи меньше текущего времени, перекидываем на  один день
        if time_obj_utc <= current_time_utc:
            time_obj_utc += timedelta(days=1)

        user_data = await state.get_data()
        user_id = user_data.get('user_id')
        task_text = user_data.get('task_text')
        task_type = user_data.get('task_type')
        async with async_session() as session:
           

            new_task = Task(user_id=user_id, task_text=task_text, task_type=task_type, status=TaskStatus.ACTIVE, time=time_obj_utc)
            session.add(new_task)
            await session.commit()
            await bot.send_message(user_id, "Задача добавлена и будет выполнена в указанное время.")
            await state.finish()  
            await handle_expired_task(session, new_task)
    except ValueError:
        await message.answer("Неверный формат времени. Попробуйте снова.")


async def handle_expired_task(session, task):
    try:
        if task.status == TaskStatus.ACTIVE:  # Проверяем, что задача все еще активна
            current_time_utc = datetime.utcnow().replace(tzinfo=None)
            task_time_utc = task.time.replace(tzinfo=None)
            if task_time_utc <= current_time_utc:
                inline_keyboard = types.InlineKeyboardMarkup()
                inline_keyboard.add(
                    types.InlineKeyboardButton(text="Завершено 🟢", callback_data=f"complete_task:{task.id}"),
                    types.InlineKeyboardButton(text="Отложить ⏳", callback_data=f"delay_task:{task.id}"),
                    types.InlineKeyboardButton(text="Пропустить 🔴", callback_data=f"skip_task:{task.id}")
                )

                # Проверяем статус задачи перед отправкой сообщения
                if task.status != TaskStatus.OVERDUE:
                    if task.task_type == "text":
                        # Отправляем текстовое сообщение
                        message = await bot.send_message(task.user_id, f"Напоминание: {task.task_text}", reply_markup=inline_keyboard)
                    elif task.task_type == "voice":
                        # Отправляем голосовое сообщение
                        message = await bot.send_voice(task.user_id, task.task_text, reply_markup=inline_keyboard)
                    elif task.task_type == "image":
                        # Отправляем изображение
                        message = await bot.send_photo(task.user_id, task.task_text, reply_markup=inline_keyboard)

                    await asyncio.sleep(30)  # Задержка перед удалением сообщения выбора действия

                    async with async_session() as delete_session:
                        await delete_session.delete(task)
                        await delete_session.commit()
                    
                    

                        # Проверяем наличие текста в сообщении перед его удалением
                        if message.text:
                            await bot.delete_message(task.user_id, message.message_id)
    except Exception as e:
        logging.exception("Ошибка при отправке уведомления: %s", e)





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
                        
                        
                        Task.time <= current_time_utc + timedelta(minutes=1)  
                    )
                )
            )
            for task in tasks.scalars():
                task_time_utc = task.time.replace(tzinfo=pytz.UTC)
                if task_time_utc <= current_time_utc:
                    print("Найдена активная задача:", task.id, task.user_id, task.task_text, task.task_type, task.status, task.time)
# Оно будет проверять лишь активные и отложеные задачики
                    if task.status not in [TaskStatus.COMPLETED, TaskStatus.OVERDUE]:  
                        await handle_expired_task(session, task)

        await asyncio.sleep(60)  # Проверяем задачи каждую минуту


async def send_reminder(session, task):
    try:
        current_time_utc = datetime.now(pytz.utc)


        task_time_utc = task.time.replace(tzinfo=pytz.utc)

        if task_time_utc <= current_time_utc and task.status != TaskStatus.OVERDUE:
            # Создаем инлайн клавиатуру с тремя кнопками: Выполнено, Отложить и Пропустить
            inline_keyboard = types.InlineKeyboardMarkup()
            inline_keyboard.add(
                types.InlineKeyboardButton(text="Выполнено🟢", callback_data=f"complete_task:{task.id}"),
                types.InlineKeyboardButton(text="Отложить⏳", callback_data=f"delay_task:{task.id}"),
                types.InlineKeyboardButton(text="Пропустить🔴", callback_data=f"skip_task:{task.id}")
            )

            if task.task_type == "text":
                await bot.send_message(task.user_id, f"Напоминание текстовой задачи: {task.task_text}", reply_markup=inline_keyboard)
            elif task.task_type == "voice":
                await bot.send_voice(task.user_id, task.task_text, reply_markup=inline_keyboard)
            elif task.task_type == "image":
                await bot.send_photo(task.user_id, task.task_text, reply_markup=inline_keyboard)

    except Exception as e:
        logging.exception("Ошибка при отправке уведомления: %s", e)


# Обработчик нажатия кнопки "Завершить"
@dp.callback_query_handler(lambda callback_query: callback_query.data.startswith('complete_task'))
async def complete_task(callback_query: types.CallbackQuery):
    task_id = int(callback_query.data.split(':')[1])  # Получаем ид задачи из callback_data
    async with async_session() as session:
        task = await session.get(Task, task_id)
        if task:
            task.status = TaskStatus.COMPLETED
            await session.commit()
            await bot.answer_callback_query(callback_query.id, "Задача завершена 🟢")
            
            # Удаляем сообщение о задаче
            await bot.delete_message(callback_query.message.chat.id, callback_query.message.message_id)
        else:
            await bot.answer_callback_query(callback_query.id, "Задача не найдена")


# Хендлер нажатия кнопки "Отложить"


async def schedule_message_deletion(task_id, chat_id, message_id):
    # Ждем 5 минут
    await asyncio.sleep(300)
    
    # Удаляем сообщение из чата
    try:
        await bot.delete_message(chat_id, message_id)
    except Exception as e:
        logging.exception("Ошибка при удалении сообщения из чата: %s", e)
# Хендлер нажатия кнопки "Отложить"
@dp.callback_query_handler(lambda callback_query: callback_query.data.startswith('delay_task'))
async def delay_task(callback_query: types.CallbackQuery, state: FSMContext):
    task_id = int(callback_query.data.split(':')[1])  # Получаем ид задачи из callback_data

    # Создаем клавиатуру с кнопками выбора интервала времени
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(
        types.InlineKeyboardButton(text="1 минуту", callback_data=f"confirm_delay:{task_id}:1"),
        types.InlineKeyboardButton(text="15 минут", callback_data=f"confirm_delay:{task_id}:15"),        
        types.InlineKeyboardButton(text="30 минут", callback_data=f"confirm_delay:{task_id}:30"),
        types.InlineKeyboardButton(text="45 минут", callback_data=f"confirm_delay:{task_id}:45"),
        types.InlineKeyboardButton(text="1 день", callback_data=f"confirm_delay:{task_id}:1440")
    )

    # Отправляем новое сообщение с запросом выбора временного интервала
    await bot.send_message(callback_query.message.chat.id, "Выберите интервал для отложения задачи:", reply_markup=keyboard)

    # Удаляем сообщение, которое вызвало callback_query
    await bot.delete_message(callback_query.message.chat.id, callback_query.message.message_id)

    # Устанавливаем задачу на удаление сообщения через некоторое время
    await schedule_message_deletion(task_id, callback_query.message.chat.id, callback_query.message.message_id)



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
            
            # Удаляем сообщение, которое вызвало callback_query
            await bot.delete_message(callback_query.message.chat.id, callback_query.message.message_id)
             # Запускаем асинхронную задачу
           
            await bot.answer_callback_query(callback_query.id, "Задача не найдена")

#Обобчик нажатия кнопки "Пропустить"
@dp.callback_query_handler(lambda callback_query: callback_query.data.startswith('skip_task'))
async def skip_task(callback_query: types.CallbackQuery):
    task_id = int(callback_query.data.split(':')[1])  # Получаем идентификатор задачи из callback_data
    async with async_session() as session:
        task = await session.get(Task, task_id)
        if task:
            task.status = TaskStatus.OVERDUE 
            await session.commit()
            await bot.answer_callback_query(callback_query.id, "Задача пропущена 🔴")
        else:
            await bot.answer_callback_query(callback_query.id, "Задача не найдена")


# Хендлер команды /help
@dp.message_handler(commands=['help'])
# нужно подумать еще и отмену типо , это нужно стырить из пиццы






# "СТАТИСТИКА"
@dp.message_handler(commands=['статистика'])
async def statistics_command(message: types.Message):
    async with async_session() as session:
        user_id = message.from_user.id
        today = datetime.now().date()

        #  фильтруем по типу задач и юзеру за сеоднящний денек
        total_tasks_today = await session.scalar(select(func.count(Task.id)).filter(
            Task.user_id == user_id,
            Task.time >= today,  # задачи после начала текущего дня
            Task.time < today + timedelta(days=1)  # Задачи до начала следующего дня
        ))
# нужно это вносить либо в инлайн меню типо или хз но 
# еще нужно сделать так чтобы можно было получить статистику за неделю\месяц 
# это идея 50 на 50 хм...
        completed_tasks_today = await session.scalar(select(func.count(Task.id)).filter(
            Task.user_id == user_id,
            Task.status == TaskStatus.COMPLETED,
            Task.time >= today,
            Task.time < today + timedelta(days=1)
        ))

        overdue_tasks_today = await session.scalar(select(func.count(Task.id)).filter(
            Task.user_id == user_id,
            Task.status == TaskStatus.OVERDUE,
            Task.time >= today,
            Task.time < today + timedelta(days=1)
        ))

        active_tasks_today = await session.scalar(select(func.count(Task.id)).filter(
            Task.user_id == user_id,
            Task.status == TaskStatus.ACTIVE,
            Task.time >= today,
            Task.time < today + timedelta(days=1)
        ))

        postponed_tasks_today = await session.scalar(select(func.count(Task.id)).filter(
            Task.user_id == user_id,
            Task.status == TaskStatus.POSTPONED,
            Task.time >= today,
            Task.time < today + timedelta(days=1)
        ))

        # рассчитываем процентное отношение
        completed_percentage_today = (completed_tasks_today / total_tasks_today) * 100 if total_tasks_today > 0 else 0
        overdue_percentage_today = (overdue_tasks_today / total_tasks_today) * 100 if total_tasks_today > 0 else 0
        active_percentage_today = (active_tasks_today / total_tasks_today) * 100 if total_tasks_today > 0 else 0
        postponed_percentage_today = (postponed_tasks_today / total_tasks_today) * 100 if total_tasks_today > 0 else 0

        # Отправляем СТАТСТИКУ юзеру
        await message.answer(f"Статистика задач за сегодня ({today}):\n"
                             f"Выполнено: {completed_percentage_today:.2f}%\n"
                             f"Просрочено: {overdue_percentage_today:.2f}%\n"
                             f"Активные: {active_percentage_today:.2f}%\n"
                             f"Отложенные: {postponed_percentage_today:.2f}%")
# иьбать оно рабоает ска УРА КАПС можно еще пару каток сыграть



async def check_tasks_periodically():
    while True:
        await asyncio.sleep(60)  # Спим 60 сек перед следующей проверкой
        await check_tasks()
# регаеи регаем 
from  aiogram.utils import executor #
#  нужно создать список и посто перебрать с for и регать 
async def main():
    await create_tables()
    dp.register_message_handler(start_command, commands=['start'])
    dp.register_message_handler(add_task, lambda message: message.text == "Добавить задачу")
    dp.register_message_handler(handle_text, content_types=ContentType.TEXT, state=States.WAITING_FOR_TASK)
    dp.register_message_handler(handle_voice, content_types=ContentType.VOICE, state=States.WAITING_FOR_TASK)
    dp.register_message_handler(handle_photo, content_types=ContentType.PHOTO, state=States.WAITING_FOR_TASK)
    dp.register_message_handler(statistics_command,commands=['статистика'])
    dp.register_message_handler(cancel_handler,Text(equals= "отмена",ignore_case = True),state="*")
    dp.register_message_handler(handle_time_input, content_types=ContentType.TEXT, state=States.WAITING_FOR_TIME)
    asyncio.create_task(check_tasks_periodically())  # Запускаем периодическую проверку задач

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.create_task(main())
    executor.start_polling(dp, skip_updates=True)