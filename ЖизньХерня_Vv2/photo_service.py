# bot/services/photo_service.py

from sqlalchemy.orm import Session
from modelsS import PhotoTask
from schemas import PhotoTaskCreate, PhotoTaskUpdate


def create_photo_task(db: Session, task: PhotoTaskCreate):
    db_task = PhotoTask(**task.dict())
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    return db_task


def get_photo_task_by_id(db: Session, task_id: int):
    return db.query(PhotoTask).filter(PhotoTask.id == task_id).first()


def update_photo_task(db: Session, task_id: int, task_update: PhotoTaskUpdate):
    db_task = db.query(PhotoTask).filter(PhotoTask.id == task_id).first()
    if db_task:
        for key, value in task_update.dict().items():
            setattr(db_task, key, value)
        db.commit()
        db.refresh(db_task)
    return db_task


def delete_photo_task(db: Session, task_id: int):
    db_task = db.query(PhotoTask).filter(PhotoTask.id == task_id).first()
    if db_task:
        db.delete(db_task)
        db.commit()
    return db_task

