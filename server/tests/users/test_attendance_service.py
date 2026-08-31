import uuid
from datetime import date

import pytest

from app.users.models import Attendance
from app.users.services import (
    calculate_next_streak_count,
    complete_daily_quest_if_eligible,
    select_daily_task_ids,
)


def attendance_on(check_in_date: date, streak_count: int) -> Attendance:
    return Attendance(
        id=uuid.uuid4(),
        user_id=uuid.uuid4(),
        check_in_date=check_in_date,
        streak_count=streak_count,
        daily_task_ids=[],
        daily_quest_completed=False,
    )


def test_first_attendance_starts_streak_at_one():
    assert calculate_next_streak_count(None, date(2026, 8, 31)) == 1


def test_yesterday_attendance_increments_streak():
    previous = attendance_on(date(2026, 8, 30), streak_count=3)

    assert calculate_next_streak_count(previous, date(2026, 8, 31)) == 4


def test_missed_day_resets_streak_to_one():
    previous = attendance_on(date(2026, 8, 29), streak_count=7)

    assert calculate_next_streak_count(previous, date(2026, 8, 31)) == 1


@pytest.mark.parametrize(
    ("previous_date", "today"),
    [
        (date(2026, 1, 31), date(2026, 2, 1)),
        (date(2026, 12, 31), date(2027, 1, 1)),
        (date(2028, 2, 29), date(2028, 3, 1)),
    ],
)
def test_streak_increments_across_calendar_boundaries(
    previous_date: date,
    today: date,
):
    previous = attendance_on(previous_date, streak_count=10)

    assert calculate_next_streak_count(previous, today) == 11


def test_daily_task_selection_uses_active_tasks_and_low_proficiency_order():
    task_ids = [uuid.uuid4() for _ in range(4)]

    class SelectionSession:
        statement = None

        def scalars(self, statement):
            self.statement = statement

            class Result:
                def all(self):
                    return task_ids

            return Result()

    db = SelectionSession()

    selected = select_daily_task_ids(db, uuid.uuid4())

    statement = str(db.statement)
    assert selected == [str(task_id) for task_id in task_ids[:3]]
    assert "tasks.is_active IS true" in statement
    assert "coalesce(user_proficiency.proficiency_level" in statement
    assert "LIMIT" in statement


def test_daily_quest_with_no_assigned_tasks_does_not_auto_complete():
    attendance = attendance_on(date(2026, 8, 31), streak_count=1)

    assert complete_daily_quest_if_eligible(attendance, set()) is False
    assert attendance.daily_quest_completed is False


def test_daily_quest_requires_every_assigned_task_to_be_correct():
    first_task_id = uuid.uuid4()
    second_task_id = uuid.uuid4()
    attendance = attendance_on(date(2026, 8, 31), streak_count=1)
    attendance.daily_task_ids = [str(first_task_id), str(second_task_id)]

    assert complete_daily_quest_if_eligible(
        attendance,
        {first_task_id},
    ) is False
    assert attendance.daily_quest_completed is False


def test_daily_quest_completion_changes_attendance_once():
    first_task_id = uuid.uuid4()
    second_task_id = uuid.uuid4()
    attendance = attendance_on(date(2026, 8, 31), streak_count=1)
    attendance.daily_task_ids = [str(first_task_id), str(second_task_id)]
    correct_task_ids = {first_task_id, second_task_id}

    assert complete_daily_quest_if_eligible(
        attendance,
        correct_task_ids,
    ) is True
    assert attendance.daily_quest_completed is True

    assert complete_daily_quest_if_eligible(
        attendance,
        correct_task_ids,
    ) is False
    assert attendance.daily_quest_completed is True
