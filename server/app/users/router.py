import uuid
from datetime import timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.exception_handlers import AppException
from app.core.schemas import ErrorResponse
from app.core.time import get_service_today
from app.db.database import get_db
from app.users.dependencies import ROLE_ADMIN, ROLE_USER, require_roles
from app.users.models import Attendance, User
from app.users.schemas import (
    AttendanceCheckInResponse,
    AttendanceResponse,
    ExternalStudentIdAvailabilityResponse,
    TodayAttendanceResponse,
    UserResponse,
)

router = APIRouter(tags=["users"])


@router.get(
    "/me",
    response_model=UserResponse,
    responses={
        status.HTTP_401_UNAUTHORIZED: {
            "model": ErrorResponse,
            "description": "현재 사용자 식별 실패",
        },
        status.HTTP_403_FORBIDDEN: {
            "model": ErrorResponse,
            "description": "허용되지 않은 사용자 역할",
        }
    },
    summary="현재 사용자 조회",
)
def get_me(
    current_user: User = Depends(require_roles(ROLE_USER, ROLE_ADMIN)),
) -> UserResponse:
    return UserResponse.model_validate(current_user)


@router.get(
    "/me/attendance/today",
    response_model=TodayAttendanceResponse,
    responses={
        status.HTTP_401_UNAUTHORIZED: {
            "model": ErrorResponse,
            "description": "현재 사용자 식별 실패",
        },
        status.HTTP_403_FORBIDDEN: {
            "model": ErrorResponse,
            "description": "허용되지 않은 사용자 역할",
        },
    },
    summary="오늘 출석 여부 조회",
)
def get_today_attendance(
    current_user: User = Depends(require_roles(ROLE_USER, ROLE_ADMIN)),
    db: Session = Depends(get_db),
) -> TodayAttendanceResponse:
    attendance = db.scalar(
        select(Attendance).where(
            Attendance.user_id == current_user.id,
            Attendance.check_in_date == get_service_today(),
        )
    )

    return TodayAttendanceResponse(
        checked_in_today=attendance is not None,
        attendance=(
            AttendanceResponse.model_validate(attendance)
            if attendance is not None
            else None
        ),
    )


@router.get(
    "/users/external-student-id/availability",
    response_model=ExternalStudentIdAvailabilityResponse,
    responses={
        status.HTTP_422_UNPROCESSABLE_CONTENT: {
            "model": ErrorResponse,
            "description": "외부 학생 ID 입력값 검증 실패",
        }
    },
    summary="외부 학생 ID 사용 가능 여부 확인",
)
def check_external_student_id_availability(
    external_student_id: Annotated[
        str,
        Query(
            min_length=1,
            max_length=100,
            pattern=r"^.*\S.*$",
        ),
    ],
    db: Session = Depends(get_db),
) -> ExternalStudentIdAvailabilityResponse:
    normalized_external_student_id = external_student_id.strip()

    existing_user_id = db.scalar(
        select(User.id)
        .where(
            User.external_student_id
            == normalized_external_student_id
        )
        .limit(1)
    )

    return ExternalStudentIdAvailabilityResponse(
        external_student_id=normalized_external_student_id,
        is_available=existing_user_id is None,
    )


@router.get(
    "/users/{user_id}",
    response_model=UserResponse,
    responses={
        status.HTTP_404_NOT_FOUND: {
            "model": ErrorResponse,
            "description": "사용자를 찾을 수 없음",
        }
    },
    summary="사용자 상세 조회",
)
def get_user(
    user_id: uuid.UUID,
    db: Session = Depends(get_db),
) -> UserResponse:
    user = db.get(User, user_id)

    if user is None:
        raise AppException(
            status_code=status.HTTP_404_NOT_FOUND,
            code="USER_NOT_FOUND",
            message="사용자를 찾을 수 없습니다.",
        )

    return UserResponse.model_validate(user)


@router.post(
    "/users/{user_id}/attendance/check-in",
    response_model=AttendanceCheckInResponse,
)
def check_in_attendance(
    user_id: uuid.UUID,
    db: Session = Depends(get_db),
) -> AttendanceCheckInResponse:
    if db.get(User, user_id) is None:
        raise AppException(
            status_code=status.HTTP_404_NOT_FOUND,
            code="USER_NOT_FOUND",
            message="사용자를 찾을 수 없습니다.",
        )

    today = get_service_today()
    yesterday = today - timedelta(days=1)
    previous_attendance = db.scalar(
        select(Attendance)
        .where(
            Attendance.user_id == user_id,
            Attendance.check_in_date < today,
        )
        .order_by(Attendance.check_in_date.desc())
        .limit(1)
    )

    streak_count = 1
    if (
        previous_attendance is not None
        and previous_attendance.check_in_date == yesterday
    ):
        streak_count = previous_attendance.streak_count + 1

    attendance = Attendance(
        user_id=user_id,
        check_in_date=today,
        streak_count=streak_count,
        daily_quest_completed=False,
    )
    db.add(attendance)

    try:
        db.flush()
    except IntegrityError as exc:
        db.rollback()
        raise AppException(
            status_code=status.HTTP_409_CONFLICT,
            code="ATTENDANCE_ALREADY_CHECKED_IN",
            message="오늘 출석이 이미 완료되었습니다.",
        ) from exc

    reward_amount = 100
    db.execute(
        update(User)
        .where(User.id == user_id)
        .values(soft_balance=User.soft_balance + reward_amount)
    )
    db.commit()
    db.refresh(attendance)

    current_soft_balance = db.scalar(
        select(User.soft_balance).where(User.id == user_id)
    )

    return AttendanceCheckInResponse(
        attendance=AttendanceResponse.model_validate(attendance),
        reward_amount=reward_amount,
        current_soft_balance=current_soft_balance,
    )


@router.get(
    "/users/{user_id}/attendances",
    response_model=list[AttendanceResponse],
)
def get_user_attendances(
    user_id: uuid.UUID,
    db: Session = Depends(get_db),
) -> list[AttendanceResponse]:
    if db.get(User, user_id) is None:
        raise AppException(
            status_code=status.HTTP_404_NOT_FOUND,
            code="USER_NOT_FOUND",
            message="사용자를 찾을 수 없습니다.",
        )

    attendances = db.scalars(
        select(Attendance)
        .where(Attendance.user_id == user_id)
        .order_by(Attendance.check_in_date.desc())
    ).all()

    return [AttendanceResponse.model_validate(item) for item in attendances]
