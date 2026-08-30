import uuid

import pytest
from pydantic import ValidationError

from app.learning.schemas import TaskAttemptCreateRequest


@pytest.mark.parametrize(
    ("context_type", "context_field"),
    [
        ("DAILY", "attendance_id"),
        ("BATTLE", "room_task_id"),
        ("RANKING", "rank_challenge_task_id"),
    ],
)
def test_attempt_request_accepts_each_linked_context(
    context_type: str,
    context_field: str,
):
    context_id = uuid.uuid4()

    request = TaskAttemptCreateRequest(
        task_id=uuid.uuid4(),
        context_type=context_type,
        submitted_code="print('cat')",
        **{context_field: context_id},
    )

    assert getattr(request, context_field) == context_id


def test_attempt_request_accepts_learning_without_context_id():
    request = TaskAttemptCreateRequest(
        task_id=uuid.uuid4(),
        context_type="LEARNING",
        submitted_code="print('cat')",
    )

    assert request.attendance_id is None
    assert request.room_task_id is None
    assert request.rank_challenge_task_id is None


@pytest.mark.parametrize(
    "payload",
    [
        {"context_type": "DAILY"},
        {"context_type": "BATTLE"},
        {"context_type": "RANKING"},
        {"context_type": "LEARNING", "attendance_id": uuid.uuid4()},
        {
            "context_type": "DAILY",
            "attendance_id": uuid.uuid4(),
            "room_task_id": uuid.uuid4(),
        },
    ],
)
def test_attempt_request_rejects_invalid_context_combinations(payload):
    with pytest.raises(ValidationError):
        TaskAttemptCreateRequest(
            task_id=uuid.uuid4(),
            submitted_code="print('cat')",
            **payload,
        )


@pytest.mark.parametrize("submitted_code", ["", " ", "\n\t"])
def test_attempt_request_rejects_empty_or_whitespace_code(submitted_code: str):
    with pytest.raises(ValidationError):
        TaskAttemptCreateRequest(
            task_id=uuid.uuid4(),
            context_type="LEARNING",
            submitted_code=submitted_code,
        )


def test_attempt_request_rejects_body_user_id():
    with pytest.raises(ValidationError):
        TaskAttemptCreateRequest(
            user_id=uuid.uuid4(),
            task_id=uuid.uuid4(),
            context_type="LEARNING",
            submitted_code="print('cat')",
        )
