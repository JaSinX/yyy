# bot/services/task_executor.py

from typing import Union
from modelsS import TextTask, VoiceTask, PhotoTask

from modelsS import PhotoTask
def execute_task(task: Union[TextTask, VoiceTask, PhotoTask]):
    # Здесь мы будем выполнять задачу в зависимости от ее типа
    if isinstance(task, TextTask):
        execute_text_task(task)
    elif isinstance(task, VoiceTask):
        execute_voice_task(task)
    elif isinstance(task, PhotoTask):
        execute_image_task(task)
    else:
        print("Не удалось определить тип задачи.")

def execute_text_task(task: TextTask):
    # Ваш код для выполнения текстовой задачи
    print(f"Выполнение текстовой задачи: {task.description}")

def execute_voice_task(task: VoiceTask):
    # Ваш код для выполнения аудиозадачи
    print("Выполнение аудиозадачи")

def execute_image_task(task: PhotoTask):
    # Ваш код для выполнения задачи с изображением
    print("Выполнение задачи с изображением")
