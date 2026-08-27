from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.learning.models import Task

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.get("")
def get_tasks(db: Session = Depends(get_db)):
    tasks = db.scalars(
        select(Task).where(Task.is_active.is_(True))
    ).all()

    return [
        {
            "id": task.id,
            "concept_id": task.concept_id,
            "type": task.type,
            "difficulty": task.difficulty,
            "template_code": task.template_code,
        }
        for task in tasks
    ]
