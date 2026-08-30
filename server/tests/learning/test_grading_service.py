import uuid
from dataclasses import dataclass

from app.learning import grading_service
from app.learning.models import Task, TaskAttempt, UserProficiency
from app.sandbox.executor import SandboxResult
from app.sandbox.grader import TestExecutionResult as ExecutionResult
from app.users.models import User


@dataclass
class FakeTask:
    test_cases: str
    concept_id: int = 1


@dataclass
class FakeUser:
    soft_balance: int = 0


@dataclass
class FakeProficiency:
    proficiency_level: int


@dataclass
class FakeAttempt:
    id: uuid.UUID
    user_id: uuid.UUID
    task_id: uuid.UUID
    submitted_code: str
    used_hint: bool = False
    status: str = "PENDING"
    is_correct: bool | None = None


class FakeSession:
    def __init__(self, state):
        self.state = state

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        return False

    def get(self, model, identity, **kwargs):
        if model is TaskAttempt:
            return self.state["attempt"]
        if model is Task:
            return self.state["task"]
        if model is User:
            return self.state["user"]
        raise AssertionError(f"unexpected model: {model}")

    def commit(self):
        self.state["commit_calls"] += 1
        if self.state["fail_commit_at"] == self.state["commit_calls"]:
            raise RuntimeError("commit failed")
        self.state["commits"].append(
            (self.state["attempt"].status, self.state["attempt"].is_correct)
        )

    def scalar(self, statement):
        statement_text = str(statement)
        if "FROM user_proficiency" in statement_text:
            return self.state["proficiency"]
        self.state["prior_queries"].append(statement_text)
        return self.state["prior_correct_attempt_id"]

    def add(self, proficiency):
        self.state["proficiency"] = proficiency

    def rollback(self):
        self.state["rolled_back"] = True
        self.state["attempt"].status = "RUNNING"
        self.state["attempt"].is_correct = None
        self.state["user"].soft_balance = self.state["initial_soft_balance"]
        self.state["proficiency"] = self.state["initial_proficiency"]


def build_state():
    user_id = uuid.uuid4()
    return {
        "user": FakeUser(),
        "attempt": FakeAttempt(
            id=uuid.uuid4(),
            user_id=user_id,
            task_id=uuid.uuid4(),
            submitted_code="def answer(): return 1",
        ),
        "task": FakeTask(
            test_cases=(
                '{"function_name":"answer",'
                '"cases":[{"args":[],"expected":1}]}'
            )
        ),
        "commits": [],
        "commit_calls": 0,
        "fail_commit_at": None,
        "rolled_back": False,
        "prior_queries": [],
        "prior_correct_attempt_id": None,
        "proficiency": None,
        "initial_proficiency": None,
        "initial_soft_balance": 0,
    }


def configure(monkeypatch):
    monkeypatch.setattr(
        grading_service,
        "get_sandbox_config",
        lambda: {
            "image": "cat-game-sandbox:local",
            "timeout_seconds": 2,
            "memory": "128m",
            "cpus": "0.5",
            "output_bytes": 4096,
            "max_concurrency": 3,
        },
    )


def execution_result(is_correct: bool) -> ExecutionResult:
    return ExecutionResult(
        total_count=1,
        passed_count=int(is_correct),
        failures=() if is_correct else ({"reason": "WRONG_ANSWER"},),
        sandbox=SandboxResult(0, "", "", False, False),
    )


def test_persists_running_then_successful_correct_result(monkeypatch):
    state = build_state()
    configure(monkeypatch)
    captured = {}

    def execute(code, test_cases, *, image, limits):
        captured.update(
            code=code,
            test_cases=test_cases,
            image=image,
            limits=limits,
        )
        return execution_result(True)

    is_first_correct = grading_service.process_attempt_grading(
        state["attempt"].id,
        session_factory=lambda: FakeSession(state),
        test_executor=execute,
    )

    assert state["commits"] == [("RUNNING", None), ("SUCCESS", True)]
    assert is_first_correct is True
    assert "task_attempts.user_id" in state["prior_queries"][0]
    assert captured["code"] == state["attempt"].submitted_code
    assert captured["test_cases"] == state["task"].test_cases
    assert captured["image"] == "cat-game-sandbox:local"
    assert captured["limits"].memory == "128m"
    assert state["user"].soft_balance == 100
    assert state["proficiency"].proficiency_level == 10


def test_persists_successful_wrong_answer(monkeypatch):
    state = build_state()
    configure(monkeypatch)

    is_first_correct = grading_service.process_attempt_grading(
        state["attempt"].id,
        session_factory=lambda: FakeSession(state),
        test_executor=lambda *args, **kwargs: execution_result(False),
    )

    assert state["commits"] == [("RUNNING", None), ("SUCCESS", False)]
    assert is_first_correct is False
    assert state["prior_queries"] == []
    assert state["user"].soft_balance == 0
    assert state["proficiency"] is None


def test_correct_retry_is_not_first_correct(monkeypatch):
    state = build_state()
    state["prior_correct_attempt_id"] = uuid.uuid4()
    configure(monkeypatch)

    is_first_correct = grading_service.process_attempt_grading(
        state["attempt"].id,
        session_factory=lambda: FakeSession(state),
        test_executor=lambda *args, **kwargs: execution_result(True),
    )

    assert is_first_correct is False
    assert state["commits"] == [("RUNNING", None), ("SUCCESS", True)]
    assert state["user"].soft_balance == 0
    assert state["proficiency"] is None


def test_halves_reward_and_proficiency_when_hint_was_used(monkeypatch):
    state = build_state()
    state["attempt"].used_hint = True
    configure(monkeypatch)

    grading_service.process_attempt_grading(
        state["attempt"].id,
        session_factory=lambda: FakeSession(state),
        test_executor=lambda *args, **kwargs: execution_result(True),
    )

    assert state["user"].soft_balance == 50
    assert state["proficiency"].proficiency_level == 5


def test_caps_existing_proficiency_at_one_hundred(monkeypatch):
    state = build_state()
    proficiency = FakeProficiency(proficiency_level=95)
    state["proficiency"] = proficiency
    state["initial_proficiency"] = proficiency
    configure(monkeypatch)

    grading_service.process_attempt_grading(
        state["attempt"].id,
        session_factory=lambda: FakeSession(state),
        test_executor=lambda *args, **kwargs: execution_result(True),
    )

    assert state["user"].soft_balance == 100
    assert state["proficiency"].proficiency_level == 100


def test_rolls_back_status_reward_and_proficiency_on_commit_error(monkeypatch):
    state = build_state()
    state["fail_commit_at"] = 2
    configure(monkeypatch)

    try:
        grading_service.process_attempt_grading(
            state["attempt"].id,
            session_factory=lambda: FakeSession(state),
            test_executor=lambda *args, **kwargs: execution_result(True),
        )
    except RuntimeError as error:
        assert str(error) == "commit failed"
    else:
        raise AssertionError("commit error was not raised")

    assert state["rolled_back"] is True
    assert state["attempt"].status == "RUNNING"
    assert state["attempt"].is_correct is None
    assert state["user"].soft_balance == 0
    assert state["proficiency"] is None


def test_persists_failed_when_sandbox_raises(monkeypatch):
    state = build_state()
    configure(monkeypatch)

    def fail(*args, **kwargs):
        raise RuntimeError("sandbox unavailable")

    grading_service.process_attempt_grading(
        state["attempt"].id,
        session_factory=lambda: FakeSession(state),
        test_executor=fail,
    )

    assert state["commits"] == [("RUNNING", None), ("FAILED", None)]


def test_does_not_regrade_non_pending_attempt(monkeypatch):
    state = build_state()
    state["attempt"].status = "SUCCESS"
    executed = False

    def execute(*args, **kwargs):
        nonlocal executed
        executed = True
        return execution_result(True)

    grading_service.process_attempt_grading(
        state["attempt"].id,
        session_factory=lambda: FakeSession(state),
        test_executor=execute,
    )

    assert executed is False
    assert state["commits"] == []
