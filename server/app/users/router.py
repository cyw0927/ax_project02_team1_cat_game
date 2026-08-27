import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
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
