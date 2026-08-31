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
        external_student_id=f"WEAK-{uuid.uuid4()}",
        username="취약 개념 사용자",
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


class WeakConceptSession:
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


def request_weak_concepts(db, user_id, *, query=""):
    def override_get_db():
        yield db

    async def request():
        transport = httpx.ASGITransport(app=app, raise_app_exceptions=False)
        async with httpx.AsyncClient(
            transport=transport,
            base_url="http://testserver",
        ) as client:
            return await client.get(
                f"/users/{user_id}/weak-concepts{query}",
                headers={"X-User-ID": str(db.user.id)},
            )

    app.dependency_overrides[get_db] = override_get_db
    try:
        return asyncio.run(request())
    finally:
        app.dependency_overrides.clear()


def test_recommends_lowest_proficiency_concepts_with_active_tasks():
    user = build_user()
    db = WeakConceptSession(user, [(2, "반복문", 0), (4, "함수", 10)])

    response = request_weak_concepts(db, user.id, query="?limit=2")

    assert response.status_code == 200
    assert response.json() == [
        {"concept_id": 2, "name": "반복문", "proficiency_level": 0},
        {"concept_id": 4, "name": "함수", "proficiency_level": 10},
    ]
    statement = str(db.statement)
    assert "coalesce(user_proficiency.proficiency_level" in statement
    assert "tasks.is_active IS true" in statement
    assert "EXISTS" in statement
    assert db.statement._limit_clause.value == 2


def test_rejects_other_users_weak_concepts():
    user = build_user()
    db = WeakConceptSession(user, [])

    response = request_weak_concepts(db, uuid.uuid4())

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "USER_ACCESS_DENIED"
    assert db.statement is None


def test_validates_recommendation_limit():
    user = build_user()
    db = WeakConceptSession(user, [])

    response = request_weak_concepts(db, user.id, query="?limit=11")

    assert response.status_code == 422
    assert db.statement is None
