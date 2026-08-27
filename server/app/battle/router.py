import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.battle.models import Room, RoomParticipant, RoomTask
from app.db.database import get_db
from app.learning.models import Task
from app.users.models import User

router = APIRouter(tags=["battle"])


class CreateRoomRequest(BaseModel):
    title: str
    host_user_id: uuid.UUID
    max_participants: int = Field(ge=1)


@router.get("/rooms")
def get_rooms(db: Session = Depends(get_db)):
    rooms = db.scalars(select(Room).order_by(Room.title)).all()

    return [
        {
            "id": room.id,
            "title": room.title,
            "host_user_id": room.host_user_id,
            "status": room.status,
            "max_participants": room.max_participants,
        }
        for room in rooms
    ]


@router.post("/rooms", status_code=status.HTTP_201_CREATED)
def create_room(payload: CreateRoomRequest, db: Session = Depends(get_db)):
    if db.get(User, payload.host_user_id) is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Host user not found",
        )

    title = payload.title.strip()
    if not title:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Room title must not be empty",
        )

    room = Room(
        title=title,
        host_user_id=payload.host_user_id,
        status="WAITING",
        max_participants=payload.max_participants,
    )
    db.add(room)
    db.commit()
    db.refresh(room)

    return {
        "id": room.id,
        "title": room.title,
        "host_user_id": room.host_user_id,
        "status": room.status,
        "max_participants": room.max_participants,
    }


@router.get("/users/{user_id}/rooms")
def get_user_rooms(
    user_id: uuid.UUID,
    db: Session = Depends(get_db),
):
    if db.get(User, user_id) is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    rows = db.execute(
        select(
            Room.id,
            Room.title,
            Room.host_user_id,
            Room.status,
            Room.max_participants,
            RoomParticipant.team_name,
            RoomParticipant.current_score,
            RoomParticipant.is_ready,
        )
        .join(RoomParticipant, RoomParticipant.room_id == Room.id)
        .where(RoomParticipant.user_id == user_id)
        .order_by(Room.title)
    ).all()

    return [
        {
            "room_id": room_id,
            "title": title,
            "host_user_id": host_user_id,
            "status": room_status,
            "max_participants": max_participants,
            "team_name": team_name,
            "current_score": current_score,
            "is_ready": is_ready,
        }
        for (
            room_id,
            title,
            host_user_id,
            room_status,
            max_participants,
            team_name,
            current_score,
            is_ready,
        ) in rows
    ]


@router.get("/rooms/{room_id}/participants")
def get_room_participants(
    room_id: uuid.UUID,
    db: Session = Depends(get_db),
):
    if db.get(Room, room_id) is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Room not found",
        )

    rows = db.execute(
        select(
            RoomParticipant.user_id,
            User.username,
            RoomParticipant.team_name,
            RoomParticipant.current_score,
            RoomParticipant.is_ready,
        )
        .join(User, User.id == RoomParticipant.user_id)
        .where(RoomParticipant.room_id == room_id)
        .order_by(User.username)
    ).all()

    return [
        {
            "user_id": user_id,
            "username": username,
            "team_name": team_name,
            "current_score": current_score,
            "is_ready": is_ready,
        }
        for user_id, username, team_name, current_score, is_ready in rows
    ]


@router.get("/rooms/{room_id}/tasks")
def get_room_tasks(
    room_id: uuid.UUID,
    db: Session = Depends(get_db),
):
    if db.get(Room, room_id) is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Room not found",
        )

    rows = db.execute(
        select(
            RoomTask.task_order,
            Task.id,
            Task.concept_id,
            Task.type,
            Task.difficulty,
            Task.template_code,
        )
        .join(Task, Task.id == RoomTask.task_id)
        .where(RoomTask.room_id == room_id)
        .order_by(RoomTask.task_order)
    ).all()

    return [
        {
            "task_order": task_order,
            "task_id": task_id,
            "concept_id": concept_id,
            "type": task_type,
            "difficulty": difficulty,
            "template_code": template_code,
        }
        for (
            task_order,
            task_id,
            concept_id,
            task_type,
            difficulty,
            template_code,
        ) in rows
    ]
