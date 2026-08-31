import asyncio
import uuid
from datetime import UTC, datetime

import httpx
from fastapi import WebSocketDisconnect

import app.battle.router as battle_router
from app.battle.models import Room, RoomParticipant, RoomTask
from app.db.database import get_db
from app.learning.models import Task
from app.main import app
from app.users.models import User


def build_user(name):
    return User(
        id=uuid.uuid4(),
        external_student_id=f"BATTLE-{uuid.uuid4()}",
        username=name,
        role="USER",
        soft_balance=0,
        hard_balance=0,
        mileage=0,
        house_level=1,
        wallpaper_item_id=None,
        floor_item_id=None,
        created_at=datetime.now(UTC),
    )


class Result:
    def __init__(self, rows):
        self.rows = rows

    def all(self):
        return self.rows


class Scalars(Result):
    pass


class BattleSession:
    def __init__(self, host, guest):
        self.users = {host.id: host, guest.id: guest}
        self.room = None
        self.participants = []
        self.room_tasks = []
        self.tasks = [
            Task(
                id=uuid.uuid4(),
                concept_id=1,
                title=f"배틀 문제 {index}",
                type="CODE",
                difficulty="BASIC",
                description="문제 설명",
                template_code="def answer():\n    pass\n",
                test_cases="SECRET",
                hint_text=None,
                is_active=True,
            )
            for index in range(1, 4)
        ]
        self.committed = False
        self.rolled_back = False

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        return False

    def get(self, model, identity, **kwargs):
        if model is User:
            return self.users.get(identity)
        if model is Room and self.room is not None and self.room.id == identity:
            return self.room
        return None

    def scalars(self, statement):
        text = str(statement)
        if "tasks.id" in text and "FROM tasks" in text:
            return Scalars([task.id for task in self.tasks])
        if "FROM room_participants" in text:
            return Scalars(list(self.participants))
        return Scalars([])

    def scalar(self, statement):
        text = str(statement)
        if "count(room_tasks.id)" in text:
            return len(self.room_tasks)
        if "room_participants.user_id" in text:
            parameter_values = set(statement.compile().params.values())
            user_id = next(
                (value for value in parameter_values if value in self.users),
                None,
            )
            for participant in self.participants:
                if participant.user_id == user_id:
                    if "room_participants.current_score" in text:
                        return participant
                    return participant.id
        return None

    def execute(self, statement):
        text = str(statement)
        if "JOIN users" in text:
            return Result(
                [
                    (
                        participant.id,
                        participant.user_id,
                        self.users[participant.user_id].username,
                        participant.team_name,
                        participant.current_score,
                        participant.is_ready,
                    )
                    for participant in self.participants
                ]
            )
        if "JOIN tasks" in text:
            task_by_id = {task.id: task for task in self.tasks}
            return Result(
                [
                    (
                        room_task.id,
                        room_task.task_id,
                        room_task.task_order,
                        task_by_id[room_task.task_id].title,
                        "CODE",
                        "BASIC",
                        "문제 설명",
                        "def answer():\n    pass\n",
                    )
                    for room_task in self.room_tasks
                ]
            )
        if "room_participants.team_name" in text and "count" in text:
            counts = {}
            for participant in self.participants:
                counts[participant.team_name] = counts.get(participant.team_name, 0) + 1
            return Result(list(counts.items()))
        return Result([])

    def add(self, row):
        if row.id is None:
            row.id = uuid.uuid4()
        if isinstance(row, Room):
            self.room = row
        elif isinstance(row, RoomParticipant):
            self.participants.append(row)
        elif isinstance(row, RoomTask):
            self.room_tasks.append(row)

    def flush(self):
        pass

    def commit(self):
        self.committed = True

    def rollback(self):
        self.rolled_back = True

    def refresh(self, row):
        pass


def request(db, user, method, path, json=None):
    def override_get_db():
        yield db

    async def send():
        transport = httpx.ASGITransport(app=app, raise_app_exceptions=False)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            return await client.request(
                method,
                path,
                headers={"X-User-ID": str(user.id)},
                json=json,
            )

    app.dependency_overrides[get_db] = override_get_db
    try:
        return asyncio.run(send())
    finally:
        app.dependency_overrides.clear()


def create_room(db, host):
    return request(
        db,
        host,
        "POST",
        "/rooms",
        {"title": "파이썬 배틀", "max_participants": 2},
    )


def test_create_room_uses_current_user_and_assigns_host_and_tasks():
    host, guest = build_user("방장"), build_user("참가자")
    db = BattleSession(host, guest)

    response = create_room(db, host)

    assert response.status_code == 201
    body = response.json()
    assert body["host_user_id"] == str(host.id)
    assert body["participants"][0]["team_name"] == "TEAM_A"
    assert body["participants"][0]["is_ready"] is True
    assert len(body["tasks"]) == 3
    assert "test_cases" not in body["tasks"][0]


def test_join_assigns_balanced_team_and_reconnects_idempotently():
    host, guest = build_user("방장"), build_user("참가자")
    db = BattleSession(host, guest)
    create_room(db, host)

    joined = request(db, guest, "POST", f"/rooms/{db.room.id}/join")
    rejoined = request(db, guest, "POST", f"/rooms/{db.room.id}/join")

    assert joined.status_code == 201
    assert joined.json()["participant"]["team_name"] == "TEAM_B"
    assert joined.json()["rejoined"] is False
    assert rejoined.status_code == 201
    assert rejoined.json()["rejoined"] is True
    assert len(db.participants) == 2


def test_full_room_rejects_another_participant():
    host, guest = build_user("방장"), build_user("참가자")
    third = build_user("세 번째")
    db = BattleSession(host, guest)
    db.users[third.id] = third
    create_room(db, host)
    request(db, guest, "POST", f"/rooms/{db.room.id}/join")

    response = request(db, third, "POST", f"/rooms/{db.room.id}/join")

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "ROOM_FULL"


def test_ready_and_host_start_conditions():
    host, guest = build_user("방장"), build_user("참가자")
    db = BattleSession(host, guest)
    create_room(db, host)
    request(db, guest, "POST", f"/rooms/{db.room.id}/join")

    too_early = request(db, host, "POST", f"/rooms/{db.room.id}/start")
    ready = request(
        db,
        guest,
        "PATCH",
        f"/rooms/{db.room.id}/ready",
        {"is_ready": True},
    )
    forbidden = request(db, guest, "POST", f"/rooms/{db.room.id}/start")
    started = request(db, host, "POST", f"/rooms/{db.room.id}/start")

    assert too_early.status_code == 409
    assert too_early.json()["error"]["code"] == "PARTICIPANTS_NOT_READY"
    assert ready.status_code == 200
    assert forbidden.status_code == 403
    assert forbidden.json()["error"]["code"] == "ROOM_HOST_REQUIRED"
    assert started.status_code == 200
    assert started.json()["status"] == "IN_PROGRESS"


def test_rejects_client_user_id_and_invalid_capacity():
    host, guest = build_user("방장"), build_user("참가자")
    db = BattleSession(host, guest)

    response = request(
        db,
        host,
        "POST",
        "/rooms",
        {"title": "배틀", "max_participants": 1, "host_user_id": str(guest.id)},
    )

    assert response.status_code == 422
    assert db.room is None


def test_websocket_sends_current_state_to_participant(monkeypatch):
    host, guest = build_user("방장"), build_user("참가자")
    db = BattleSession(host, guest)
    create_room(db, host)
    monkeypatch.setattr(battle_router, "SessionLocal", lambda: db)

    class FakeWebSocket:
        def __init__(self):
            self.accepted = False
            self.messages = []

        async def accept(self):
            self.accepted = True

        async def send_json(self, message_body):
            self.messages.append(message_body)

        async def receive_text(self):
            raise WebSocketDisconnect()

        async def close(self, code):
            raise AssertionError(f"unexpected close: {code}")

    websocket = FakeWebSocket()
    asyncio.run(battle_router.room_websocket(websocket, db.room.id, host.id))
    message_body = websocket.messages[0]

    assert websocket.accepted is True
    assert message_body["type"] == "ROOM_STATE"
    assert message_body["data"]["room_id"] == str(db.room.id)
    assert message_body["data"]["participants"][0]["user_id"] == str(host.id)
