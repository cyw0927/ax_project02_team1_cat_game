import uuid
from dataclasses import dataclass

from app.battle.models import Room, RoomParticipant, RoomTask
from app.battle.service import apply_battle_correct_result
from app.learning.models import TaskAttempt
from app.users.models import User


class Rows:
    def __init__(self, rows):
        self.rows = rows

    def all(self):
        return self.rows


@dataclass
class FakeAttempt:
    id: uuid.UUID
    user_id: uuid.UUID
    context_type: str
    room_task_id: uuid.UUID


class BattleScoreSession:
    def __init__(self, *, prior_correct=None, prior_solved=2):
        self.user = User(soft_balance=0)
        self.room = Room(id=uuid.uuid4(), status="IN_PROGRESS")
        self.room_task = RoomTask(id=uuid.uuid4(), room_id=self.room.id)
        self.participant = RoomParticipant(
            room_id=self.room.id,
            user_id=uuid.uuid4(),
            team_name="TEAM_A",
            current_score=200,
            is_ready=True,
        )
        self.prior_correct = prior_correct
        self.prior_solved = prior_solved

    def get(self, model, identity, **kwargs):
        if model is RoomTask:
            return self.room_task
        if model is Room:
            return self.room
        return None

    def scalar(self, statement):
        text = str(statement)
        if "FROM room_participants" in text:
            return self.participant
        if "count(DISTINCT task_attempts.room_task_id)" in text:
            return self.prior_solved
        if "count(room_tasks.id)" in text:
            return 3
        if "FROM task_attempts" in text:
            return self.prior_correct
        return None

    def execute(self, statement):
        return Rows([("TEAM_A", self.participant.current_score), ("TEAM_B", 100)])

    def scalars(self, statement):
        text = str(statement)
        if "room_participants.user_id" in text:
            return Rows([self.participant.user_id])
        if "FROM users" in text:
            return Rows([self.user])
        return Rows([])

    def flush(self):
        pass


def test_first_correct_scores_finishes_room_and_rewards_winner():
    db = BattleScoreSession()
    attempt = FakeAttempt(
        id=uuid.uuid4(),
        user_id=db.participant.user_id,
        context_type="BATTLE",
        room_task_id=db.room_task.id,
    )

    applied = apply_battle_correct_result(db, attempt)

    assert applied is True
    assert db.participant.current_score == 300
    assert db.room.status == "FINISHED"
    assert db.user.soft_balance == 200


def test_duplicate_correct_does_not_score_or_finish_again():
    db = BattleScoreSession(prior_correct=uuid.uuid4())
    attempt = FakeAttempt(
        id=uuid.uuid4(),
        user_id=db.participant.user_id,
        context_type="BATTLE",
        room_task_id=db.room_task.id,
    )

    applied = apply_battle_correct_result(db, attempt)

    assert applied is False
    assert db.participant.current_score == 200
    assert db.room.status == "IN_PROGRESS"
