import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.learning.models import Task
from app.ranking.models import (
    RankChallenge,
    RankChallengeTask,
    RankingGroup,
    RankingParticipant,
)
from app.users.models import User

router = APIRouter(tags=["ranking"])


class StartRankChallengeRequest(BaseModel):
    user_id: uuid.UUID
    task_ids: list[uuid.UUID] = Field(min_length=1)
    expires_at: datetime


class SaveRankChallengeTaskRequest(BaseModel):
    user_id: uuid.UUID
    saved_code: str


@router.get("/ranking-groups")
def get_ranking_groups(db: Session = Depends(get_db)):
    groups = db.scalars(select(RankingGroup).order_by(RankingGroup.name)).all()

    return [
        {
            "id": group.id,
            "name": group.name,
            "owner_user_id": group.owner_user_id,
        }
        for group in groups
    ]


@router.get("/ranking-groups/{group_id}/participants")
def get_ranking_participants(
    group_id: uuid.UUID,
    db: Session = Depends(get_db),
):
    if db.get(RankingGroup, group_id) is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ranking group not found",
        )

    rows = db.execute(
        select(
            RankingParticipant.user_id,
            User.username,
            RankingParticipant.current_rank_score,
        )
        .join(User, User.id == RankingParticipant.user_id)
        .where(RankingParticipant.group_id == group_id)
        .order_by(RankingParticipant.current_rank_score.desc())
    ).all()

    return [
        {
            "user_id": user_id,
            "username": username,
            "current_rank_score": current_rank_score,
        }
        for user_id, username, current_rank_score in rows
    ]


@router.get("/users/{user_id}/ranking-groups")
def get_user_ranking_groups(
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
            RankingGroup.id,
            RankingGroup.name,
            RankingGroup.owner_user_id,
            RankingParticipant.current_rank_score,
        )
        .join(
            RankingParticipant,
            RankingParticipant.group_id == RankingGroup.id,
        )
        .where(RankingParticipant.user_id == user_id)
        .order_by(RankingGroup.name)
    ).all()

    return [
        {
            "group_id": group_id,
            "name": name,
            "owner_user_id": owner_user_id,
            "current_rank_score": current_rank_score,
        }
        for group_id, name, owner_user_id, current_rank_score in rows
    ]


@router.get("/users/{user_id}/rank-challenges")
def get_user_rank_challenges(
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
            RankChallenge.id,
            RankChallenge.group_id,
            RankingGroup.name,
            RankChallenge.status,
            RankChallenge.started_at,
            RankChallenge.expires_at,
        )
        .join(RankingGroup, RankingGroup.id == RankChallenge.group_id)
        .where(RankChallenge.user_id == user_id)
        .order_by(RankChallenge.started_at.desc())
    ).all()

    return [
        {
            "challenge_id": challenge_id,
            "group_id": group_id,
            "group_name": group_name,
            "status": challenge_status,
            "started_at": started_at,
            "expires_at": expires_at,
        }
        for (
            challenge_id,
            group_id,
            group_name,
            challenge_status,
            started_at,
            expires_at,
        ) in rows
    ]


@router.get("/rank-challenges/{challenge_id}/tasks")
def get_rank_challenge_tasks(
    challenge_id: uuid.UUID,
    db: Session = Depends(get_db),
):
    if db.get(RankChallenge, challenge_id) is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Rank challenge not found",
        )

    rows = db.execute(
        select(
            RankChallengeTask.task_order,
            Task.id,
            Task.concept_id,
            Task.type,
            Task.difficulty,
            Task.template_code,
            RankChallengeTask.is_passed,
            RankChallengeTask.saved_code,
        )
        .join(Task, Task.id == RankChallengeTask.task_id)
        .where(RankChallengeTask.challenge_id == challenge_id)
        .order_by(RankChallengeTask.task_order)
    ).all()

    return [
        {
            "task_order": task_order,
            "task_id": task_id,
            "concept_id": concept_id,
            "type": task_type,
            "difficulty": difficulty,
            "template_code": template_code,
            "is_passed": is_passed,
            "has_saved_code": saved_code is not None,
        }
        for (
            task_order,
            task_id,
            concept_id,
            task_type,
            difficulty,
            template_code,
            is_passed,
            saved_code,
        ) in rows
    ]


@router.post(
    "/ranking-groups/{group_id}/rank-challenges",
    status_code=status.HTTP_201_CREATED,
)
def start_rank_challenge(
    group_id: uuid.UUID,
    payload: StartRankChallengeRequest,
    db: Session = Depends(get_db),
):
    now = datetime.now(timezone.utc)
    expires_at = payload.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if expires_at <= now:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="expires_at must be in the future",
        )

    participant = db.scalar(
        select(RankingParticipant).where(
            RankingParticipant.group_id == group_id,
            RankingParticipant.user_id == payload.user_id,
        )
    )
    if participant is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ranking participant not found",
        )

    active_challenge = db.scalar(
        select(RankChallenge.id).where(
            RankChallenge.group_id == group_id,
            RankChallenge.user_id == payload.user_id,
            RankChallenge.status == "IN_PROGRESS",
            RankChallenge.expires_at > now,
        )
    )
    if active_challenge is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An active rank challenge already exists",
        )

    if len(set(payload.task_ids)) != len(payload.task_ids):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="task_ids must not contain duplicates",
        )

    active_task_ids = set(
        db.scalars(
            select(Task.id).where(
                Task.id.in_(payload.task_ids),
                Task.is_active.is_(True),
            )
        ).all()
    )
    if active_task_ids != set(payload.task_ids):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="One or more active tasks were not found",
        )

    challenge = RankChallenge(
        user_id=payload.user_id,
        group_id=group_id,
        status="IN_PROGRESS",
        started_at=now,
        expires_at=expires_at,
    )
    db.add(challenge)
    db.flush()
    for task_order, task_id in enumerate(payload.task_ids, start=1):
        db.add(
            RankChallengeTask(
                challenge_id=challenge.id,
                task_id=task_id,
                is_passed=False,
                saved_code=None,
                task_order=task_order,
            )
        )
    db.commit()
    db.refresh(challenge)
    return {
        "challenge_id": challenge.id,
        "group_id": challenge.group_id,
        "user_id": challenge.user_id,
        "status": challenge.status,
        "started_at": challenge.started_at,
        "expires_at": challenge.expires_at,
        "task_count": len(payload.task_ids),
    }


@router.put("/rank-challenges/{challenge_id}/tasks/{task_id}/code")
def save_rank_challenge_code(
    challenge_id: uuid.UUID,
    task_id: uuid.UUID,
    payload: SaveRankChallengeTaskRequest,
    db: Session = Depends(get_db),
):
    challenge = db.scalar(
        select(RankChallenge).where(
            RankChallenge.id == challenge_id,
            RankChallenge.user_id == payload.user_id,
        )
    )
    if challenge is None:
        raise HTTPException(status_code=404, detail="Rank challenge not found")

    now = datetime.now(timezone.utc)
    if challenge.status != "IN_PROGRESS" or challenge.expires_at <= now:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Rank challenge is not active",
        )

    challenge_task = db.scalar(
        select(RankChallengeTask).where(
            RankChallengeTask.challenge_id == challenge_id,
            RankChallengeTask.task_id == task_id,
        )
    )
    if challenge_task is None:
        raise HTTPException(status_code=404, detail="Rank challenge task not found")

    challenge_task.saved_code = payload.saved_code
    db.commit()
    db.refresh(challenge_task)
    return {
        "challenge_id": challenge_id,
        "task_id": task_id,
        "saved": True,
    }
