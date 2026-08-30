import uuid
from collections.abc import Collection
from datetime import date, timedelta

from sqlalchemy import and_, func, select
from sqlalchemy.orm import Session

from app.learning.models import Task, UserProficiency
from app.users.models import Attendance


DAILY_TASK_LIMIT = 3


def select_daily_task_ids(
    db: Session,
    user_id: uuid.UUID,
) -> list[str]:
    """활성 문제 중 숙련도가 낮은 개념의 문제를 최대 3개 선택한다."""

    task_ids = db.scalars(
        select(Task.id)
        .outerjoin(
            UserProficiency,
            and_(
                UserProficiency.user_id == user_id,
                UserProficiency.concept_id == Task.concept_id,
            ),
        )
        .where(Task.is_active.is_(True))
        .order_by(
            func.coalesce(UserProficiency.proficiency_level, 0),
            Task.concept_id,
            Task.id,
        )
        .limit(DAILY_TASK_LIMIT)
    ).all()

    return [str(task_id) for task_id in task_ids[:DAILY_TASK_LIMIT]]


def calculate_next_streak_count(
    previous_attendance: Attendance | None,
    today: date,
) -> int:
    """가장 최근 과거 출석을 기준으로 오늘의 연속 출석 일수를 계산한다."""

    if (
        previous_attendance is not None
        and previous_attendance.check_in_date == today - timedelta(days=1)
    ):
        return previous_attendance.streak_count + 1

    return 1


def complete_daily_quest_if_eligible(
    attendance: Attendance,
    correct_task_ids: Collection[uuid.UUID],
) -> bool:
    """배정된 문제를 모두 맞힌 경우 완료 상태를 한 번만 변경한다.

    문제 0개인 출석은 자동 완료하지 않는다. 실제 정답 attempt 조회와 보상
    지급은 채점 transaction이 담당하며, 이 함수도 그 transaction 안에서
    호출한다.
    """

    assigned_task_ids = {
        uuid.UUID(task_id)
        for task_id in attendance.daily_task_ids
    }

    if not assigned_task_ids or not assigned_task_ids.issubset(correct_task_ids):
        return False

    if attendance.daily_quest_completed:
        return False

    attendance.daily_quest_completed = True
    return True
