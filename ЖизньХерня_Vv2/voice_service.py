

# bot/services/voice_service.py

from sqlalchemy.orm import Session
from modelsS import VoiceTask
from schemas import VoiceTaskCreate, VoiceTaskUpdate


def create_voice_task(db: Session, task: VoiceTaskCreate):
    db_task = VoiceTask(**task.dict())
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    return db_task


def get_voice_task_by_id(db: Session, task_id: int):
    return db.query(VoiceTask).filter(VoiceTask.id == task_id).first()


def update_voice_task(db: Session, task_id: int, task_update: VoiceTaskUpdate):
    db_task = db.query(VoiceTask).filter(VoiceTask.id == task_id).first()
    if db_task:
        for key, value in task_update.dict().items():
            setattr(db_task, key, value)
        db.commit()
        db.refresh(db_task)
    return db_task


def delete_voice_task(db: Session, task_id: int):
    db_task = db.query(VoiceTask).filter(VoiceTask.id == task_id).first()
    if db_task:
        db.delete(db_task)
        db.commit()
    return db_task
