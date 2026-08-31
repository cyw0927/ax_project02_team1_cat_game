import asyncio
import json
import uuid

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.battle.models import Room, RoomParticipant, RoomTask
from app.battle.schemas import (
    BattleStateResponse,
    CreateRoomRequest,
    JoinRoomResponse,
    ParticipantResponse,
    ReadyResponse,
    RoomDetailResponse,
    RoomStatusResponse,
    RoomSummaryResponse,
    RoomTaskResponse,
    SetReadyRequest,
)
from app.core import config
from app.core.exception_handlers import AppException
from app.db.database import SessionLocal, get_db
from app.learning.models import Task
from app.users.dependencies import ROLE_ADMIN, ROLE_USER, require_roles
from app.users.models import User


router = APIRouter(tags=["battle"])

ROOM_WAITING = "WAITING"
ROOM_IN_PROGRESS = "IN_PROGRESS"
ROOM_FINISHED = "FINISHED"
TEAM_A = "TEAM_A"
TEAM_B = "TEAM_B"
BATTLE_TASK_LIMIT = 3


def _commit(db: Session) -> None:
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise


def _get_room(db: Session, room_id: uuid.UUID, *, lock: bool = False) -> Room:
    room = (
        db.get(Room, room_id, with_for_update=True)
        if lock
        else db.get(Room, room_id)
    )
    if room is None:
        raise AppException(
            status_code=status.HTTP_404_NOT_FOUND,
            code="ROOM_NOT_FOUND",
            message="배틀방을 찾을 수 없습니다.",
        )
    return room


def _participant_rows(db: Session, room_id: uuid.UUID):
    return db.execute(
        select(
            RoomParticipant.id,
            RoomParticipant.user_id,
            User.username,
            RoomParticipant.team_name,
            RoomParticipant.current_score,
            RoomParticipant.is_ready,
        )
        .join(User, User.id == RoomParticipant.user_id)
        .where(RoomParticipant.room_id == room_id)
        .order_by(RoomParticipant.team_name, User.username)
    ).all()


def _participants(db: Session, room: Room) -> list[ParticipantResponse]:
    return [
        ParticipantResponse(
            participant_id=participant_id,
            user_id=user_id,
            username=username,
            team_name=team_name,
            current_score=current_score,
            is_ready=is_ready,
            is_host=user_id == room.host_user_id,
        )
        for (
            participant_id,
            user_id,
            username,
            team_name,
            current_score,
            is_ready,
        ) in _participant_rows(db, room.id)
    ]


def _tasks(db: Session, room_id: uuid.UUID) -> list[RoomTaskResponse]:
    rows = db.execute(
        select(
            RoomTask.id,
            Task.id,
            RoomTask.task_order,
            Task.title,
            Task.type,
            Task.difficulty,
            Task.description,
            Task.template_code,
        )
        .join(Task, Task.id == RoomTask.task_id)
        .where(RoomTask.room_id == room_id)
        .order_by(RoomTask.task_order)
    ).all()
    return [
        RoomTaskResponse(
            room_task_id=room_task_id,
            task_id=task_id,
            task_order=task_order,
            title=title,
            type=task_type,
            difficulty=difficulty,
            description=description,
            template_code=template_code,
        )
        for (
            room_task_id,
            task_id,
            task_order,
            title,
            task_type,
            difficulty,
            description,
            template_code,
        ) in rows
    ]


def _winning_team(participants: list[ParticipantResponse]) -> str | None:
    if not participants:
        return None
    scores = {TEAM_A: 0, TEAM_B: 0}
    for participant in participants:
        scores[participant.team_name] += participant.current_score
    if scores[TEAM_A] == scores[TEAM_B]:
        return None
    return max(scores, key=scores.get)


def _detail(db: Session, room: Room) -> RoomDetailResponse:
    participants = _participants(db, room)
    return RoomDetailResponse(
        id=room.id,
        title=room.title,
        host_user_id=room.host_user_id,
        status=room.status,
        max_participants=room.max_participants,
        participant_count=len(participants),
        participants=participants,
        tasks=_tasks(db, room.id),
        winning_team=(
            _winning_team(participants) if room.status == ROOM_FINISHED else None
        ),
    )


@router.get("/rooms", response_model=list[RoomSummaryResponse])
def get_rooms(db: Session = Depends(get_db)) -> list[RoomSummaryResponse]:
    rows = db.execute(
        select(
            Room.id,
            Room.title,
            Room.host_user_id,
            Room.status,
            Room.max_participants,
            func.count(RoomParticipant.id),
        )
        .outerjoin(RoomParticipant, RoomParticipant.room_id == Room.id)
        .group_by(Room.id)
        .order_by(Room.status, Room.title)
    ).all()
    return [
        RoomSummaryResponse(
            id=room_id,
            title=title,
            host_user_id=host_user_id,
            status=room_status,
            max_participants=max_participants,
            participant_count=participant_count,
        )
        for room_id, title, host_user_id, room_status, max_participants, participant_count in rows
    ]


@router.post(
    "/rooms",
    response_model=RoomDetailResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_room(
    payload: CreateRoomRequest,
    current_user: User = Depends(require_roles(ROLE_USER, ROLE_ADMIN)),
    db: Session = Depends(get_db),
) -> RoomDetailResponse:
    task_ids = db.scalars(
        select(Task.id)
        .where(Task.is_active.is_(True))
        .order_by(Task.id)
        .limit(BATTLE_TASK_LIMIT)
    ).all()
    if not task_ids:
        raise AppException(
            status_code=status.HTTP_409_CONFLICT,
            code="NO_ACTIVE_BATTLE_TASKS",
            message="배틀에 사용할 활성 문제가 없습니다.",
        )
    room = Room(
        title=payload.title.strip(),
        host_user_id=current_user.id,
        status=ROOM_WAITING,
        max_participants=payload.max_participants,
    )
    db.add(room)
    db.flush()
    db.add(
        RoomParticipant(
            room_id=room.id,
            user_id=current_user.id,
            team_name=TEAM_A,
            current_score=0,
            is_ready=True,
        )
    )
    for order, task_id in enumerate(task_ids, start=1):
        db.add(RoomTask(room_id=room.id, task_id=task_id, task_order=order))
    _commit(db)
    return _detail(db, room)


@router.get("/rooms/{room_id}", response_model=RoomDetailResponse)
def get_room_detail(room_id: uuid.UUID, db: Session = Depends(get_db)) -> RoomDetailResponse:
    return _detail(db, _get_room(db, room_id))


@router.post(
    "/rooms/{room_id}/join",
    response_model=JoinRoomResponse,
    status_code=status.HTTP_201_CREATED,
)
def join_room(
    room_id: uuid.UUID,
    current_user: User = Depends(require_roles(ROLE_USER, ROLE_ADMIN)),
    db: Session = Depends(get_db),
) -> JoinRoomResponse:
    room = _get_room(db, room_id, lock=True)
    existing = db.scalar(
        select(RoomParticipant).where(
            RoomParticipant.room_id == room_id,
            RoomParticipant.user_id == current_user.id,
        )
    )
    if existing is not None:
        participant = next(
            row for row in _participants(db, room) if row.user_id == current_user.id
        )
        return JoinRoomResponse(participant=participant, rejoined=True)
    if room.status != ROOM_WAITING:
        raise AppException(
            status_code=status.HTTP_409_CONFLICT,
            code="ROOM_NOT_JOINABLE",
            message="참가할 수 없는 상태의 배틀방입니다.",
        )
    team_counts = dict(
        db.execute(
            select(RoomParticipant.team_name, func.count(RoomParticipant.id))
            .where(RoomParticipant.room_id == room_id)
            .group_by(RoomParticipant.team_name)
        ).all()
    )
    participant_count = sum(team_counts.values())
    if participant_count >= room.max_participants:
        raise AppException(
            status_code=status.HTTP_409_CONFLICT,
            code="ROOM_FULL",
            message="배틀방 정원이 가득 찼습니다.",
        )
    team_name = (
        TEAM_A
        if team_counts.get(TEAM_A, 0) <= team_counts.get(TEAM_B, 0)
        else TEAM_B
    )
    participant = RoomParticipant(
        room_id=room_id,
        user_id=current_user.id,
        team_name=team_name,
        current_score=0,
        is_ready=False,
    )
    db.add(participant)
    _commit(db)
    db.refresh(participant)
    return JoinRoomResponse(
        participant=ParticipantResponse(
            participant_id=participant.id,
            user_id=current_user.id,
            username=current_user.username,
            team_name=team_name,
            current_score=0,
            is_ready=False,
            is_host=False,
        ),
        rejoined=False,
    )


@router.patch("/rooms/{room_id}/ready", response_model=ReadyResponse)
def set_participant_ready(
    room_id: uuid.UUID,
    payload: SetReadyRequest,
    current_user: User = Depends(require_roles(ROLE_USER, ROLE_ADMIN)),
    db: Session = Depends(get_db),
) -> ReadyResponse:
    room = _get_room(db, room_id, lock=True)
    if room.status != ROOM_WAITING:
        raise AppException(
            status_code=status.HTTP_409_CONFLICT,
            code="READY_STATE_LOCKED",
            message="대기 중인 방에서만 준비 상태를 변경할 수 있습니다.",
        )
    participant = db.scalar(
        select(RoomParticipant).where(
            RoomParticipant.room_id == room_id,
            RoomParticipant.user_id == current_user.id,
        )
    )
    if participant is None:
        raise AppException(
            status_code=status.HTTP_404_NOT_FOUND,
            code="ROOM_PARTICIPANT_NOT_FOUND",
            message="배틀방 참가자를 찾을 수 없습니다.",
        )
    participant.is_ready = payload.is_ready
    _commit(db)
    return ReadyResponse(
        participant_id=participant.id,
        room_id=room_id,
        user_id=current_user.id,
        is_ready=participant.is_ready,
    )


@router.post("/rooms/{room_id}/start", response_model=RoomStatusResponse)
def start_room(
    room_id: uuid.UUID,
    current_user: User = Depends(require_roles(ROLE_USER, ROLE_ADMIN)),
    db: Session = Depends(get_db),
) -> RoomStatusResponse:
    room = _get_room(db, room_id, lock=True)
    if room.host_user_id != current_user.id:
        raise AppException(
            status_code=status.HTTP_403_FORBIDDEN,
            code="ROOM_HOST_REQUIRED",
            message="방장만 배틀을 시작할 수 있습니다.",
        )
    if room.status != ROOM_WAITING:
        raise AppException(
            status_code=status.HTTP_409_CONFLICT,
            code="ROOM_NOT_WAITING",
            message="대기 중인 방만 시작할 수 있습니다.",
        )
    participants = db.scalars(
        select(RoomParticipant).where(RoomParticipant.room_id == room_id)
    ).all()
    if len(participants) < 2:
        raise AppException(
            status_code=status.HTTP_409_CONFLICT,
            code="NOT_ENOUGH_PARTICIPANTS",
            message="배틀 시작에는 두 명 이상이 필요합니다.",
        )
    if any(not participant.is_ready for participant in participants):
        raise AppException(
            status_code=status.HTTP_409_CONFLICT,
            code="PARTICIPANTS_NOT_READY",
            message="모든 참가자가 준비해야 합니다.",
        )
    task_count = db.scalar(
        select(func.count(RoomTask.id)).where(RoomTask.room_id == room_id)
    )
    if not task_count:
        raise AppException(
            status_code=status.HTTP_409_CONFLICT,
            code="ROOM_TASKS_REQUIRED",
            message="배틀 문제가 필요합니다.",
        )
    room.status = ROOM_IN_PROGRESS
    _commit(db)
    return RoomStatusResponse(room_id=room.id, status=room.status)


@router.get("/rooms/{room_id}/tasks", response_model=list[RoomTaskResponse])
def get_room_tasks(
    room_id: uuid.UUID,
    current_user: User = Depends(require_roles(ROLE_USER, ROLE_ADMIN)),
    db: Session = Depends(get_db),
) -> list[RoomTaskResponse]:
    _get_room(db, room_id)
    participant_id = db.scalar(
        select(RoomParticipant.id).where(
            RoomParticipant.room_id == room_id,
            RoomParticipant.user_id == current_user.id,
        )
    )
    if participant_id is None:
        raise AppException(
            status_code=status.HTTP_403_FORBIDDEN,
            code="ROOM_PARTICIPANT_REQUIRED",
            message="배틀방 참가자만 문제를 조회할 수 있습니다.",
        )
    return _tasks(db, room_id)


@router.get("/rooms/{room_id}/state", response_model=BattleStateResponse)
def get_battle_state(
    room_id: uuid.UUID,
    db: Session = Depends(get_db),
) -> BattleStateResponse:
    room = _get_room(db, room_id)
    participants = _participants(db, room)
    return BattleStateResponse(
        room_id=room.id,
        status=room.status,
        winning_team=(
            _winning_team(participants) if room.status == ROOM_FINISHED else None
        ),
        participants=participants,
    )


def _websocket_state(room_id: uuid.UUID, user_id: uuid.UUID) -> dict:
    with SessionLocal() as db:
        room = db.get(Room, room_id)
        participant = db.scalar(
            select(RoomParticipant.id).where(
                RoomParticipant.room_id == room_id,
                RoomParticipant.user_id == user_id,
            )
        )
        if room is None or participant is None:
            return {}
        return get_battle_state(room_id, db).model_dump(mode="json")


@router.websocket("/ws/rooms/{room_id}")
async def room_websocket(
    websocket: WebSocket,
    room_id: uuid.UUID,
    user_id: uuid.UUID,
) -> None:
    if config.APP_ENV.lower() not in {"development", "test"}:
        await websocket.close(code=4401)
        return
    initial_state = _websocket_state(room_id, user_id)
    if not initial_state:
        await websocket.close(code=4403)
        return
    await websocket.accept()
    previous = ""
    try:
        while True:
            state = _websocket_state(room_id, user_id)
            serialized = json.dumps(state, sort_keys=True)
            if serialized != previous:
                await websocket.send_json({"type": "ROOM_STATE", "data": state})
                previous = serialized
            try:
                await asyncio.wait_for(websocket.receive_text(), timeout=1.0)
            except TimeoutError:
                continue
    except WebSocketDisconnect:
        return
