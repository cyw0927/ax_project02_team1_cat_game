import uuid
from datetime import date, timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.users.models import Attendance, User

router = APIRouter(tags=["users"])


@router.get("/users/{user_id}")
def get_user(user_id: uuid.UUID, db: Session = Depends(get_db)):
    user = db.get(User, user_id)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    return {
        "id": user.id,
        "username": user.username,
        "role": user.role,
        "balance": user.balance,
        "mileage": user.mileage,
        "house_level": user.house_level,
        "wallpaper_item_id": user.wallpaper_item_id,
        "floor_item_id": user.floor_item_id,
        "created_at": user.created_at,
    }


@router.post("/users/{user_id}/attendance/check-in")
def check_in_attendance(
    user_id: uuid.UUID,
    db: Session = Depends(get_db),
):
    if db.get(User, user_id) is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    today = date.today()
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
    )
    db.add(attendance)

    try:
        db.flush()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Attendance already checked in today",
        ) from exc

    reward_amount = 100
    db.execute(
        update(User)
        .where(User.id == user_id)
        .values(balance=User.balance + reward_amount)
    )
    db.commit()
    db.refresh(attendance)

    current_balance = db.scalar(
        select(User.balance).where(User.id == user_id)
    )

    return {
        "attendance_id": attendance.id,
        "check_in_date": attendance.check_in_date,
        "streak_count": attendance.streak_count,
        "reward_amount": reward_amount,
        "current_balance": current_balance,
    }


@router.get("/users/{user_id}/attendances")
def get_user_attendances(
    user_id: uuid.UUID,
    db: Session = Depends(get_db),
):
    if db.get(User, user_id) is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    attendances = db.scalars(
        select(Attendance)
        .where(Attendance.user_id == user_id)
        .order_by(Attendance.check_in_date.desc())
    ).all()

    return [
        {
            "id": attendance.id,
            "check_in_date": attendance.check_in_date,
            "streak_count": attendance.streak_count,
        }
        for attendance in attendances
    ]
