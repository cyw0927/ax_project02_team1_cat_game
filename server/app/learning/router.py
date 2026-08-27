import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.learning.models import Concept, Task, UserProficiency
from app.users.models import User

router = APIRouter(tags=["learning"])


class AttemptRequest(BaseModel):
    task_id: uuid.UUID
    submitted_code: str


@router.get("/tasks")
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


@router.get("/users/{user_id}/proficiency")
def get_user_proficiency(
    user_id: uuid.UUID,
    db: Session = Depends(get_db),
):
    if db.get(User, user_id) is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    rows = db.execute(
        select(
            Concept.id,
            Concept.name,
            UserProficiency.proficiency_level,
        )
        .join(UserProficiency, UserProficiency.concept_id == Concept.id)
        .where(UserProficiency.user_id == user_id)
        .order_by(Concept.id)
    ).all()

    return [
        {
            "concept_id": concept_id,
            "concept_name": concept_name,
            "proficiency_level": proficiency_level,
        }
        for concept_id, concept_name, proficiency_level in rows
    ]


@router.post("/attempts")
def submit_attempt(payload: AttemptRequest, db: Session = Depends(get_db)):
    task = db.scalar(
        select(Task).where(
            Task.id == payload.task_id,
            Task.is_active.is_(True),
        )
    )

    if task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Active task not found",
        )

    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Docker sandbox grading is not connected yet",
    )
