import asyncio
import uuid
from datetime import UTC, datetime

import httpx

from app.db.database import get_db
from app.learning.models import Task, TaskAttempt
from app.main import app
from app.users.models import User


def build_user() -> User:
    return User(
        id=uuid.uuid4(),
        external_student_id=f"ATTEMPT-{uuid.uuid4()}",
        username="제출 테스트 사용자",
        role="USER",
        soft_balance=0,
        hard_balance=0,
        mileage=0,
        house_level=1,
        wallpaper_item_id=None,
        floor_item_id=None,
        created_at=datetime.now(UTC),
    )


def build_task() -> Task:
    return Task(
        id=uuid.uuid4(),
        concept_id=1,
        title="제출 테스트 문제",
        type="CODE",
        difficulty="BASIC",
        description="설명",
        template_code="pass",
        test_cases='{"cases": []}',
        hint_text=None,
        is_active=True,
    )


class AttemptSession:
    def __init__(self, user: User, scalar_results: list[object]) -> None:
        self.user = user
        self.scalar_results = iter(scalar_results)
        self.added_attempt: TaskAttempt | None = None
        self.committed = False
        self.rolled_back = False

    def get(self, model, identity):
        if model is User and identity == self.user.id:
            return self.user
        return None

    def scalar(self, statement):
        return next(self.scalar_results)

    def add(self, attempt: TaskAttempt) -> None:
        self.added_attempt = attempt

    def commit(self) -> None:
        self.committed = True
        assert self.added_attempt is not None
        self.added_attempt.id = uuid.uuid4()

    def rollback(self) -> None:
        self.rolled_back = True

    def refresh(self, attempt: TaskAttempt) -> None:
        pass


def post_attempt(db: AttemptSession, payload: dict) -> httpx.Response:
    def override_get_db():
        yield db

    async def request() -> httpx.Response:
        transport = httpx.ASGITransport(
            app=app,
            raise_app_exceptions=False,
        )
        async with httpx.AsyncClient(
            transport=transport,
            base_url="http://testserver",
        ) as client:
            return await client.post(
                "/attempts",
                headers={"X-User-ID": str(db.user.id)},
                json=payload,
            )

    app.dependency_overrides[get_db] = override_get_db
    try:
        return asyncio.run(request())
    finally:
        app.dependency_overrides.clear()


def learning_payload(task_id: uuid.UUID) -> dict:
    return {
        "task_id": str(task_id),
        "context_type": "LEARNING",
        "submitted_code": "print('cat')",
        "used_hint": False,
    }


def test_submit_attempt_uses_current_user_and_stores_pending():
    user = build_user()
    task = build_task()
    db = AttemptSession(user, [task])

    response = post_attempt(db, learning_payload(task.id))

    assert response.status_code == 202
    assert db.committed is True
    assert db.added_attempt is not None
    assert db.added_attempt.user_id == user.id
    assert db.added_attempt.context_type == "LEARNING"
    assert db.added_attempt.status == "PENDING"
    assert db.added_attempt.is_correct is None
    assert response.json()["status"] == "PENDING"
    assert response.json()["is_correct"] is None


def test_submit_attempt_rejects_body_user_id():
    user = build_user()
    task = build_task()
    db = AttemptSession(user, [task])
    payload = learning_payload(task.id)
    payload["user_id"] = str(uuid.uuid4())

    response = post_attempt(db, payload)

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"
    assert db.added_attempt is None


def test_submit_attempt_returns_404_for_inactive_or_missing_task():
    user = build_user()
    db = AttemptSession(user, [None])

    response = post_attempt(db, learning_payload(uuid.uuid4()))

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "TASK_NOT_FOUND"
    assert db.added_attempt is None


def test_submit_daily_attempt_validates_owned_assigned_context():
    user = build_user()
    task = build_task()
    attendance_id = uuid.uuid4()
    db = AttemptSession(user, [task, attendance_id])
    payload = {
        "task_id": str(task.id),
        "context_type": "DAILY",
        "attendance_id": str(attendance_id),
        "submitted_code": "print('daily cat')",
    }

    response = post_attempt(db, payload)

    assert response.status_code == 202
    assert db.added_attempt is not None
    assert db.added_attempt.attendance_id == attendance_id


def test_submit_attempt_rejects_unowned_or_mismatched_context():
    user = build_user()
    task = build_task()
    db = AttemptSession(user, [task, None])
    payload = {
        "task_id": str(task.id),
        "context_type": "DAILY",
        "attendance_id": str(uuid.uuid4()),
        "submitted_code": "print('daily cat')",
    }

    response = post_attempt(db, payload)

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "ATTEMPT_CONTEXT_NOT_FOUND"
    assert db.added_attempt is None


class CommitFailureSession(AttemptSession):
    def commit(self) -> None:
        raise RuntimeError("commit failed")


def test_submit_attempt_rolls_back_when_pending_insert_fails():
    user = build_user()
    task = build_task()
    db = CommitFailureSession(user, [task])

    response = post_attempt(db, learning_payload(task.id))

    assert response.status_code == 500
    assert db.rolled_back is True
