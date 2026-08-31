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
        external_student_id=f"PROF-{uuid.uuid4()}",
        username="숙련도 사용자",
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


class ProficiencySession:
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


def request_proficiency(db, user_id):
    def override_get_db():
        yield db

    async def request():
        transport = httpx.ASGITransport(app=app, raise_app_exceptions=False)
        async with httpx.AsyncClient(
            transport=transport,
            base_url="http://testserver",
        ) as client:
            return await client.get(
                f"/users/{user_id}/proficiency",
                headers={"X-User-ID": str(db.user.id)},
            )

    app.dependency_overrides[get_db] = override_get_db
    try:
        return asyncio.run(request())
    finally:
        app.dependency_overrides.clear()


def test_returns_all_concepts_with_zero_default():
    user = build_user()
    db = ProficiencySession(user, [(1, "변수", 0), (2, "반복문", 20)])

    response = request_proficiency(db, user.id)

    assert response.status_code == 200
    assert response.json() == [
        {"concept_id": 1, "concept_name": "변수", "proficiency_level": 0},
        {"concept_id": 2, "concept_name": "반복문", "proficiency_level": 20},
    ]
    statement = str(db.statement)
    assert "LEFT OUTER JOIN user_proficiency" in statement
    assert "coalesce(user_proficiency.proficiency_level" in statement


def test_rejects_other_users_proficiency():
    user = build_user()
    db = ProficiencySession(user, [])

    response = request_proficiency(db, uuid.uuid4())

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "USER_ACCESS_DENIED"
    assert db.statement is None
