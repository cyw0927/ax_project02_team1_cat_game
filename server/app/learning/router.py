import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.learning.models import Concept, Task, TaskAttempt, UserProficiency
from app.users.models import User

router = APIRouter(tags=["learning"])


class AttemptRequest(BaseModel):
    user_id: uuid.UUID
    task_id: uuid.UUID
    submitted_code: str
    used_hint: bool = False


@router.get("/concepts")
def get_concepts(db: Session = Depends(get_db)):
    concepts = db.scalars(select(Concept).order_by(Concept.id)).all()

    return [
        {
            "id": concept.id,
            "name": concept.name,
        }
        for concept in concepts
    ]


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


@router.get("/users/{user_id}/attempts")
def get_user_attempts(
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
            TaskAttempt.id,
            TaskAttempt.task_id,
            Task.concept_id,
            Task.type,
            Task.difficulty,
            TaskAttempt.status,
            TaskAttempt.is_correct,
            TaskAttempt.used_hint,
            TaskAttempt.attempted_at,
        )
        .join(Task, Task.id == TaskAttempt.task_id)
        .where(TaskAttempt.user_id == user_id)
        .order_by(TaskAttempt.attempted_at.desc())
    ).all()

    return [
        {
            "attempt_id": attempt_id,
            "task_id": task_id,
            "concept_id": concept_id,
            "type": task_type,
            "difficulty": difficulty,
            "status": attempt_status,
            "is_correct": is_correct,
            "used_hint": used_hint,
            "attempted_at": attempted_at,
        }
        for (
            attempt_id,
            task_id,
            concept_id,
            task_type,
            difficulty,
            attempt_status,
            is_correct,
            used_hint,
            attempted_at,
        ) in rows
    ]


@router.get("/attempts/{attempt_id}")
def get_attempt_result(
    attempt_id: uuid.UUID,
    db: Session = Depends(get_db),
):
    row = db.execute(
        select(
            TaskAttempt.id,
            TaskAttempt.task_id,
            Task.concept_id,
            Task.type,
            Task.difficulty,
            TaskAttempt.status,
            TaskAttempt.is_correct,
            TaskAttempt.used_hint,
            TaskAttempt.attempted_at,
        )
        .join(Task, Task.id == TaskAttempt.task_id)
        .where(TaskAttempt.id == attempt_id)
    ).one_or_none()

    if row is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Attempt not found",
        )

    (
        found_attempt_id,
        task_id,
        concept_id,
        task_type,
        difficulty,
        attempt_status,
        is_correct,
        used_hint,
        attempted_at,
    ) = row

    return {
        "attempt_id": found_attempt_id,
        "task_id": task_id,
        "concept_id": concept_id,
        "type": task_type,
        "difficulty": difficulty,
        "status": attempt_status,
        "is_correct": is_correct,
        "used_hint": used_hint,
        "attempted_at": attempted_at,
    }


@router.post("/attempts", status_code=status.HTTP_202_ACCEPTED)
def submit_attempt(payload: AttemptRequest, db: Session = Depends(get_db)):
    if db.get(User, payload.user_id) is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

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

    attempt = TaskAttempt(
        user_id=payload.user_id,
        task_id=payload.task_id,
        submitted_code=payload.submitted_code,
        status="PENDING",
        is_correct=False,
        used_hint=payload.used_hint,
        attempted_at=datetime.now(timezone.utc),
    )
    db.add(attempt)
    db.commit()
    db.refresh(attempt)

    return {
        "attempt_id": attempt.id,
        "status": attempt.status,
        "is_correct": attempt.is_correct,
        "used_hint": attempt.used_hint,
        "attempted_at": attempt.attempted_at,
    }
