import uuid
from datetime import date, datetime

from pydantic import Field

from app.core.schemas import SchemaBase


class UserCreateRequest(SchemaBase):
    """사용자 생성 요청."""

    external_student_id: str = Field(
        min_length=1,
        max_length=100,
    )
    username: str = Field(
        min_length=1,
        max_length=50,
    )


class UserSummaryResponse(SchemaBase):
    """다른 화면에서 사용하는 사용자 기본 정보."""

    id: uuid.UUID
    username: str
    role: str


class UserResponse(SchemaBase):
    """사용자 상세 정보 응답."""

    id: uuid.UUID
    external_student_id: str
    username: str
    role: str
    soft_balance: int
    hard_balance: int
    mileage: int
    house_level: int
    wallpaper_item_id: int | None
    floor_item_id: int | None
    created_at: datetime


class ExternalStudentIdAvailabilityResponse(SchemaBase):
    """외부 학생 ID 사용 가능 여부 응답."""

    external_student_id: str
    is_available: bool


class AttendanceResponse(SchemaBase):
    """출석 정보 응답."""

    id: uuid.UUID
    user_id: uuid.UUID
    check_in_date: date
    streak_count: int
    daily_quest_completed: bool


class TodayAttendanceResponse(SchemaBase):
    """오늘 출석 여부 응답."""

    checked_in_today: bool
    attendance: AttendanceResponse | None = None


class AttendanceCheckInResponse(SchemaBase):
    """출석 체크 및 보상 지급 결과 응답."""

    attendance: AttendanceResponse
    reward_amount: int = Field(ge=0)
    current_soft_balance: int = Field(ge=0)