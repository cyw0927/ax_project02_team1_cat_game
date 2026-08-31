import uuid

from sqlalchemy import distinct, func, select
from sqlalchemy.orm import Session

from app.battle.models import Room, RoomParticipant, RoomTask
from app.learning.models import TaskAttempt
from app.users.models import User


BATTLE_CORRECT_SCORE = 100
BATTLE_WIN_REWARD = 200
ROOM_IN_PROGRESS = "IN_PROGRESS"
ROOM_FINISHED = "FINISHED"


def apply_battle_correct_result(db: Session, attempt: TaskAttempt) -> bool:
    """첫 정답 점수를 반영하고 완주 시 승리 팀에 한 번만 보상한다."""

    if attempt.context_type != "BATTLE" or attempt.room_task_id is None:
        return False
    room_task = db.get(RoomTask, attempt.room_task_id)
    if room_task is None:
        raise RuntimeError("RoomTask not found while applying battle result")
    room = db.get(Room, room_task.room_id, with_for_update=True)
    if room is None or room.status != ROOM_IN_PROGRESS:
        return False
    participant = db.scalar(
        select(RoomParticipant)
        .where(
            RoomParticipant.room_id == room.id,
            RoomParticipant.user_id == attempt.user_id,
        )
        .with_for_update()
    )
    if participant is None:
        raise RuntimeError("RoomParticipant not found while applying battle result")
    prior_correct = db.scalar(
        select(TaskAttempt.id)
        .where(
            TaskAttempt.user_id == attempt.user_id,
            TaskAttempt.room_task_id == attempt.room_task_id,
            TaskAttempt.id != attempt.id,
            TaskAttempt.status == "SUCCESS",
            TaskAttempt.is_correct.is_(True),
        )
        .limit(1)
    )
    if prior_correct is not None:
        return False

    participant.current_score += BATTLE_CORRECT_SCORE
    db.flush()
    total_task_count = db.scalar(
        select(func.count(RoomTask.id)).where(RoomTask.room_id == room.id)
    )
    prior_solved_count = db.scalar(
        select(func.count(distinct(TaskAttempt.room_task_id)))
        .join(RoomTask, RoomTask.id == TaskAttempt.room_task_id)
        .where(
            RoomTask.room_id == room.id,
            TaskAttempt.user_id == attempt.user_id,
            TaskAttempt.id != attempt.id,
            TaskAttempt.status == "SUCCESS",
            TaskAttempt.is_correct.is_(True),
        )
    )
    if prior_solved_count + 1 < total_task_count:
        return True

    room.status = ROOM_FINISHED
    db.flush()
    team_scores = dict(
        db.execute(
            select(
                RoomParticipant.team_name,
                func.sum(RoomParticipant.current_score),
            )
            .where(RoomParticipant.room_id == room.id)
            .group_by(RoomParticipant.team_name)
        ).all()
    )
    if not team_scores:
        return True
    best_score = max(team_scores.values())
    winners = [team for team, score in team_scores.items() if score == best_score]
    if len(winners) != 1:
        return True
    winner_ids = db.scalars(
        select(RoomParticipant.user_id).where(
            RoomParticipant.room_id == room.id,
            RoomParticipant.team_name == winners[0],
        )
    ).all()
    winning_users = db.scalars(
        select(User)
        .where(User.id.in_(sorted(winner_ids)))
        .order_by(User.id)
        .with_for_update()
    ).all()
    for user in winning_users:
        user.soft_balance += BATTLE_WIN_REWARD
    return True
