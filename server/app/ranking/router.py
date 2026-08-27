import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.ranking.models import RankingGroup, RankingParticipant
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
