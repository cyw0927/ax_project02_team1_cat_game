import asyncio
import uuid
from datetime import date

import httpx

from app.db.database import get_db
from app.main import app
from app.users.models import Attendance, User
from app.users.router import check_in_attendance


class AvailabilitySession:
    def __init__(self, existing_user_id: uuid.UUID | None) -> None:
        self.existing_user_id = existing_user_id

    def scalar(self, statement):
        return self.existing_user_id


def get_availability(
    existing_user_id: uuid.UUID | None,
    external_student_id: str,
) -> httpx.Response:
    def override_get_db():
        yield AvailabilitySession(existing_user_id)

    async def request() -> httpx.Response:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(
            transport=transport,
            base_url="http://testserver",
        ) as client:
            return await client.get(
                "/users/external-student-id/availability",
                params={"external_student_id": external_student_id},
            )

    app.dependency_overrides[get_db] = override_get_db
    try:
        return asyncio.run(request())
    finally:
        app.dependency_overrides.clear()


def test_external_student_id_is_available_and_normalized():
    response = get_availability(
        existing_user_id=None,
        external_student_id="  NEW-001  ",
    )

    assert response.status_code == 200
    assert response.json() == {
        "external_student_id": "NEW-001",
        "is_available": True,
    }


def test_existing_external_student_id_is_not_available():
    response = get_availability(
        existing_user_id=uuid.uuid4(),
        external_student_id="DEV-001",
    )

    assert response.status_code == 200
    assert response.json() == {
        "external_student_id": "DEV-001",
        "is_available": False,
    }


def test_external_student_id_rejects_blank_input():
    response = get_availability(
        existing_user_id=None,
        external_student_id="   ",
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"
    assert response.json()["error"]["details"][0]["field"] == (
        "query.external_student_id"
    )


class AttendanceSession:
    def __init__(self, user_id: uuid.UUID) -> None:
        self.user = User(
            id=user_id,
            external_student_id="DEV-001",
            username="개발용 학습자",
            role="USER",
            soft_balance=1000,
            hard_balance=100,
            mileage=0,
            house_level=1,
        )
        self.scalar_results = iter((None, 1100))
        self.added_attendance: Attendance | None = None
        self.executed_statement = None

    def get(self, model, identity):
        return self.user

    def scalar(self, statement):
        return next(self.scalar_results)

    def add(self, attendance: Attendance) -> None:
        self.added_attendance = attendance

    def flush(self) -> None:
        assert self.added_attendance is not None
        self.added_attendance.id = uuid.uuid4()

    def execute(self, statement) -> None:
        self.executed_statement = statement

    def commit(self) -> None:
        pass

    def refresh(self, attendance: Attendance) -> None:
        pass


def test_attendance_check_in_uses_current_orm_columns():
    user_id = uuid.uuid4()
    db = AttendanceSession(user_id)

    response = check_in_attendance(user_id=user_id, db=db)

    assert db.added_attendance is not None
    assert db.added_attendance.check_in_date == date.today()
    assert db.added_attendance.daily_quest_completed is False
    assert "soft_balance" in str(db.executed_statement)
    assert response.current_soft_balance == 1100
    assert response.attendance.user_id == user_id
