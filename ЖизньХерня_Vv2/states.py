# bot/states.py

from aiogram.dispatcher.filters.state import StatesGroup, State


class TextTaskState(StatesGroup):
    WaitingForDescription = State()
    WaitingForTime = State()

# bot/states.py

from aiogram.dispatcher.filters.state import StatesGroup, State


class PhotoTaskState(StatesGroup):
    WaitingForDescription = State()
    WaitingForTime = State()


class VoiceTaskState(StatesGroup):
    WaitingForDescription = State()
