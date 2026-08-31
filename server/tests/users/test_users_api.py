import asyncio
import uuid
from datetime import UTC, datetime, timedelta

import httpx
import pytest
from sqlalchemy.exc import IntegrityError

from app.core import config
from app.core.exception_handlers import AppException
from app.core.time import get_service_today
from app.db.database import get_db
from app.main import app
from app.users.dependencies import ROLE_ADMIN, require_roles
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


class CurrentUserSession:
    def __init__(
        self,
        user: User | None,
        attendance: Attendance | None = None,
    ) -> None:
        self.user = user
        self.attendance = attendance

    def get(self, model, identity):
        if self.user is not None and self.user.id == identity:
            return self.user
        return None

    def scalar(self, statement):
        return self.attendance


def get_me_response(
    user: User | None,
    header_value: str | None,
    *,
    path: str = "/me",
    attendance: Attendance | None = None,
) -> httpx.Response:
    def override_get_db():
        yield CurrentUserSession(user, attendance)

    async def request() -> httpx.Response:
        transport = httpx.ASGITransport(app=app)
        headers = {}
        if header_value is not None:
            headers["X-User-ID"] = header_value

        async with httpx.AsyncClient(
            transport=transport,
            base_url="http://testserver",
        ) as client:
            return await client.get(path, headers=headers)

    app.dependency_overrides[get_db] = override_get_db
    try:
        return asyncio.run(request())
    finally:
        app.dependency_overrides.clear()


def build_user(user_id: uuid.UUID, role: str = "USER") -> User:
    return User(
        id=user_id,
        external_student_id="DEV-001",
        username="개발용 학습자",
        role=role,
        soft_balance=1000,
        hard_balance=100,
        mileage=0,
        house_level=1,
        wallpaper_item_id=None,
        floor_item_id=None,
        created_at=datetime.now(UTC),
    )


def test_get_me_returns_user_identified_by_development_header():
    user_id = uuid.uuid4()

    response = get_me_response(
        user=build_user(user_id),
        header_value=str(user_id),
    )

    assert response.status_code == 200
    assert response.json()["id"] == str(user_id)
    assert response.json()["external_student_id"] == "DEV-001"


def test_get_me_requires_current_user_header():
    response = get_me_response(user=None, header_value=None)

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "CURRENT_USER_ID_REQUIRED"


def test_get_me_rejects_invalid_current_user_id():
    response = get_me_response(user=None, header_value="not-a-uuid")

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "INVALID_CURRENT_USER_ID"


def test_get_me_rejects_unknown_current_user():
    response = get_me_response(user=None, header_value=str(uuid.uuid4()))

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "CURRENT_USER_NOT_FOUND"


def test_get_me_rejects_development_header_in_production(monkeypatch):
    user_id = uuid.uuid4()
    monkeypatch.setattr(config, "APP_ENV", "production")

    response = get_me_response(
        user=build_user(user_id),
        header_value=str(user_id),
    )

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "AUTHENTICATION_REQUIRED"


def test_get_me_allows_admin_role():
    user_id = uuid.uuid4()

    response = get_me_response(
        user=build_user(user_id, role="ADMIN"),
        header_value=str(user_id),
    )

    assert response.status_code == 200
    assert response.json()["role"] == "ADMIN"


def test_get_me_rejects_unsupported_role():
    user_id = uuid.uuid4()

    response = get_me_response(
        user=build_user(user_id, role="GUEST"),
        header_value=str(user_id),
    )

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "INSUFFICIENT_ROLE"


def test_admin_role_guard_accepts_admin_and_rejects_user():
    admin_guard = require_roles(ROLE_ADMIN)
    admin = build_user(uuid.uuid4(), role="ADMIN")
    user = build_user(uuid.uuid4(), role="USER")

    assert admin_guard(current_user=admin) is admin

    with pytest.raises(AppException) as exc_info:
        admin_guard(current_user=user)

    assert exc_info.value.status_code == 403
    assert exc_info.value.code == "INSUFFICIENT_ROLE"


def test_role_guard_rejects_unknown_role_configuration():
    with pytest.raises(ValueError, match="Unsupported role"):
        require_roles("GUEST")


def build_attendance(user_id: uuid.UUID) -> Attendance:
    return Attendance(
        id=uuid.uuid4(),
        user_id=user_id,
        check_in_date=get_service_today(),
        streak_count=3,
        daily_quest_completed=False,
    )


def test_get_today_attendance_returns_not_checked_in():
    user_id = uuid.uuid4()

    response = get_me_response(
        user=build_user(user_id),
        header_value=str(user_id),
        path="/me/attendance/today",
    )

    assert response.status_code == 200
    assert response.json() == {
        "checked_in_today": False,
        "attendance": None,
    }


def test_get_today_attendance_returns_attendance_details():
    user_id = uuid.uuid4()
    attendance = build_attendance(user_id)

    response = get_me_response(
        user=build_user(user_id),
        header_value=str(user_id),
        path="/me/attendance/today",
        attendance=attendance,
    )

    assert response.status_code == 200
    assert response.json()["checked_in_today"] is True
    assert response.json()["attendance"] == {
        "id": str(attendance.id),
        "user_id": str(user_id),
        "check_in_date": attendance.check_in_date.isoformat(),
        "streak_count": 3,
        "daily_quest_completed": False,
    }


class AttendanceSession:
    def __init__(
        self,
        user_id: uuid.UUID,
        previous_attendance: Attendance | None = None,
        daily_task_ids: list[uuid.UUID] | None = None,
    ) -> None:
        self.user = build_user(user_id)
        self.scalar_results = iter((previous_attendance, 1100))
        self.daily_task_ids = daily_task_ids or []
        self.added_attendance: Attendance | None = None
        self.executed_statement = None
        self.committed = False
        self.rolled_back = False

    def get(self, model, identity):
        return self.user

    def scalar(self, statement):
        return next(self.scalar_results)

    def scalars(self, statement):
        class Result:
            def __init__(self, values):
                self.values = values

            def all(self):
                return self.values

        return Result(self.daily_task_ids)

    def add(self, attendance: Attendance) -> None:
        self.added_attendance = attendance

    def flush(self) -> None:
        assert self.added_attendance is not None
        self.added_attendance.id = uuid.uuid4()

    def execute(self, statement) -> None:
        self.executed_statement = statement

    def commit(self) -> None:
        self.committed = True

    def rollback(self) -> None:
        self.rolled_back = True

    def refresh(self, attendance: Attendance) -> None:
        pass


def post_current_attendance(
    db: AttendanceSession,
    header_value: str | None,
) -> httpx.Response:
    def override_get_db():
        yield db

    async def request() -> httpx.Response:
        transport = httpx.ASGITransport(
            app=app,
            raise_app_exceptions=False,
        )
        headers = {}
        if header_value is not None:
            headers["X-User-ID"] = header_value

        async with httpx.AsyncClient(
            transport=transport,
            base_url="http://testserver",
        ) as client:
            return await client.post(
                "/me/attendance/check-in",
                headers=headers,
            )

    app.dependency_overrides[get_db] = override_get_db
    try:
        return asyncio.run(request())
    finally:
        app.dependency_overrides.clear()


def test_current_user_attendance_check_in_creates_attendance_and_reward():
    user_id = uuid.uuid4()
    task_ids = [uuid.uuid4() for _ in range(4)]
    db = AttendanceSession(user_id, daily_task_ids=task_ids)

    response = post_current_attendance(db, str(user_id))

    assert response.status_code == 201
    assert db.committed is True
    assert db.rolled_back is False
    assert db.added_attendance is not None
    assert db.added_attendance.daily_task_ids == [
        str(task_id) for task_id in task_ids[:3]
    ]
    assert response.json()["attendance"]["user_id"] == str(user_id)
    assert response.json()["reward_amount"] == 100
    assert response.json()["current_soft_balance"] == 1100


def test_current_user_attendance_check_in_requires_identity():
    user_id = uuid.uuid4()
    db = AttendanceSession(user_id)

    response = post_current_attendance(db, None)

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "CURRENT_USER_ID_REQUIRED"
    assert db.added_attendance is None
    assert db.committed is False


class DuplicateAttendanceSession(AttendanceSession):
    def flush(self) -> None:
        raise IntegrityError(
            "INSERT INTO attendances",
            {},
            Exception("uq_attendances_user_date"),
        )


def test_duplicate_attendance_rolls_back_without_reward():
    user_id = uuid.uuid4()
    db = DuplicateAttendanceSession(user_id)

    response = post_current_attendance(db, str(user_id))

    assert response.status_code == 409
    assert response.json()["error"]["code"] == (
        "ATTENDANCE_ALREADY_CHECKED_IN"
    )
    assert db.rolled_back is True
    assert db.executed_statement is None
    assert db.committed is False


class RewardFailureAttendanceSession(AttendanceSession):
    def execute(self, statement) -> None:
        self.executed_statement = statement
        raise RuntimeError("reward update failed")


def test_reward_failure_rolls_back_attendance_transaction():
    user_id = uuid.uuid4()
    db = RewardFailureAttendanceSession(user_id)

    response = post_current_attendance(db, str(user_id))

    assert response.status_code == 500
    assert response.json()["error"]["code"] == "INTERNAL_SERVER_ERROR"
    assert db.rolled_back is True
    assert db.committed is False


def test_attendance_model_has_daily_unique_constraint():
    constraint_names = {
        constraint.name
        for constraint in Attendance.__table__.constraints
        if constraint.name
    }

    assert "uq_attendances_user_date" in constraint_names
    assert "ck_attendances_daily_task_ids_array" in constraint_names
    assert "daily_task_ids" in Attendance.__table__.columns


def test_attendance_check_in_uses_current_orm_columns():
    user_id = uuid.uuid4()
    db = AttendanceSession(user_id)

    response = check_in_attendance(user_id=user_id, db=db)

    assert db.added_attendance is not None
    assert db.added_attendance.check_in_date == get_service_today()
    assert db.added_attendance.daily_quest_completed is False
    assert "soft_balance" in str(db.executed_statement)
    assert response.current_soft_balance == 1100
    assert response.attendance.user_id == user_id


def test_attendance_check_in_applies_consecutive_streak():
    user_id = uuid.uuid4()
    previous_attendance = Attendance(
        id=uuid.uuid4(),
        user_id=user_id,
        check_in_date=get_service_today() - timedelta(days=1),
        streak_count=3,
        daily_quest_completed=True,
    )
    db = AttendanceSession(user_id, previous_attendance)

    response = check_in_attendance(user_id=user_id, db=db)

    assert response.attendance.streak_count == 4
