import uuid

from fastapi import APIRouter, Depends, HTTPException, status
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
