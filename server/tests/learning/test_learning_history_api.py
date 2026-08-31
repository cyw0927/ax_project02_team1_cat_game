import asyncio
import uuid
from datetime import UTC, datetime

import httpx

from app.db.database import get_db
from app.main import app
from app.users.models import User


def build_user() -> User:
    return User(
        id=uuid.uuid4(),
        external_student_id=f"HISTORY-{uuid.uuid4()}",
        username="학습 이력 사용자",
        role="USER",
        soft_balance=0,
        hard_balance=0,
        mileage=0,
        house_level=1,
        wallpaper_item_id=None,
        floor_item_id=None,
        created_at=datetime.now(UTC),
    )


class Rows:
    def __init__(self, rows):
        self.rows = rows

    def all(self):
        return self.rows


class HistorySession:
    def __init__(self, user, rows):
        self.user = user
        self.rows = rows
        self.statement = None

    def get(self, model, identity):
        if model is User and identity == self.user.id:
            return self.user
        return None

    def execute(self, statement):
        self.statement = statement
        return Rows(self.rows)


def request_history(db, user_id, *, query=""):
    def override_get_db():
        yield db

    async def request():
        transport = httpx.ASGITransport(app=app, raise_app_exceptions=False)
        async with httpx.AsyncClient(
            transport=transport,
            base_url="http://testserver",
        ) as client:
            return await client.get(
                f"/users/{user_id}/attempts{query}",
                headers={"X-User-ID": str(db.user.id)},
            )

    app.dependency_overrides[get_db] = override_get_db
    try:
        return asyncio.run(request())
    finally:
        app.dependency_overrides.clear()


def test_returns_only_public_learning_history_fields():
    user = build_user()
    attempted_at = datetime.now(UTC)
    row = (
        uuid.uuid4(),
        uuid.uuid4(),
        1,
        "CODE",
        "BASIC",
        "LEARNING",
        "SUCCESS",
        True,
        False,
        attempted_at,
    )
    db = HistorySession(user, [row])

    response = request_history(db, user.id, query="?limit=10&offset=5")

    assert response.status_code == 200
    assert response.json()[0] == {
        "attempt_id": str(row[0]),
        "task_id": str(row[1]),
        "context_type": "LEARNING",
        "status": "SUCCESS",
        "is_correct": True,
        "used_hint": False,
        "attempted_at": attempted_at.isoformat().replace("+00:00", "Z"),
        "concept_id": 1,
        "task_type": "CODE",
        "difficulty": "BASIC",
    }
    assert "submitted_code" not in response.text
    assert "test_cases" not in response.text
    assert db.statement._limit_clause.value == 10
    assert db.statement._offset_clause.value == 5


def test_rejects_other_users_history_without_querying_attempts():
    user = build_user()
    db = HistorySession(user, [])

    response = request_history(db, uuid.uuid4())

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "USER_ACCESS_DENIED"
    assert db.statement is None


def test_validates_pagination_range():
    user = build_user()
    db = HistorySession(user, [])

    response = request_history(db, user.id, query="?limit=101&offset=-1")

    assert response.status_code == 422
    assert db.statement is None
