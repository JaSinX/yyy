
# bot/services/text_task_service.py

from sqlalchemy.orm import Session
from modelsS import TextTask
import schemas
# Создание новой текстовой задачи
def create_text_task(db: Session, task: schemas.TextTaskCreate):
    db_task = TextTask(**task.dict())
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    return db_task

# Получение списка всех текстовых задач
def get_all_text_tasks(db: Session):
    return db.query(TextTask).all()

# Получение текстовой задачи по ее идентификатору
def get_text_task_by_id(db: Session, task_id: int):
    return db.query(TextTask).filter(TextTask.id == task_id).first()

# Обновление информации о текстовой задаче
def update_text_task(db: Session, task_id: int, task_update: schemas.TextTaskUpdate):
    db_task = db.query(TextTask).filter(TextTask.id == task_id).first()
    if db_task:
        for key, value in task_update.dict().items():
            setattr(db_task, key, value)
        db.commit()
        db.refresh(db_task)
    return db_task

# Удаление текстовой задачи по ее идентификатору
def delete_text_task(db: Session, task_id: int):
    db_task = db.query(TextTask).filter(TextTask.id == task_id).first()
    if db_task:
        db.delete(db_task)
        db.commit()
    return db_task
