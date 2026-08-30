import asyncio
import uuid
from datetime import UTC, datetime

import httpx
import pytest

from app.db.database import get_db
from app.learning.models import TaskAttempt
from app.main import app
from app.users.models import User


def build_user() -> User:
    return User(
        id=uuid.uuid4(),
        external_student_id=f"RESULT-{uuid.uuid4()}",
        username="결과 조회 사용자",
        role="USER",
        soft_balance=0,
        hard_balance=0,
        mileage=0,
        house_level=1,
        wallpaper_item_id=None,
        floor_item_id=None,
        created_at=datetime.now(UTC),
    )


def build_attempt(user: User, *, status: str, is_correct: bool | None):
    return TaskAttempt(
        id=uuid.uuid4(),
        user_id=user.id,
        task_id=uuid.uuid4(),
        context_type="LEARNING",
        attendance_id=None,
        room_task_id=None,
        rank_challenge_task_id=None,
        submitted_code="def answer(): return 1",
        status=status,
        is_correct=is_correct,
        used_hint=False,
        attempted_at=datetime.now(UTC),
    )


class ResultSession:
    def __init__(self, user, attempt):
        self.user = user
        self.attempt = attempt

    def get(self, model, identity):
        if model is User and identity == self.user.id:
            return self.user
        return None

    def scalar(self, statement):
        return self.attempt


def get_result(db: ResultSession, attempt_id: uuid.UUID) -> httpx.Response:
    def override_get_db():
        yield db

    async def request():
        transport = httpx.ASGITransport(app=app, raise_app_exceptions=False)
        async with httpx.AsyncClient(
            transport=transport,
            base_url="http://testserver",
        ) as client:
            return await client.get(
                f"/attempts/{attempt_id}",
                headers={"X-User-ID": str(db.user.id)},
            )

    app.dependency_overrides[get_db] = override_get_db
    try:
        return asyncio.run(request())
    finally:
        app.dependency_overrides.clear()


@pytest.mark.parametrize(
    ("status", "is_correct"),
    [
        ("PENDING", None),
        ("RUNNING", None),
        ("SUCCESS", True),
        ("SUCCESS", False),
        ("FAILED", None),
    ],
)
def test_returns_owned_attempt_result(status, is_correct):
    user = build_user()
    attempt = build_attempt(user, status=status, is_correct=is_correct)

    response = get_result(ResultSession(user, attempt), attempt.id)

    assert response.status_code == 200
    assert response.json() == {
        "attempt_id": str(attempt.id),
        "task_id": str(attempt.task_id),
        "context_type": "LEARNING",
        "status": status,
        "is_correct": is_correct,
        "used_hint": False,
        "attempted_at": attempt.attempted_at.isoformat().replace("+00:00", "Z"),
    }


def test_hides_missing_or_unowned_attempt():
    user = build_user()
    response = get_result(ResultSession(user, None), uuid.uuid4())

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "ATTEMPT_NOT_FOUND"
