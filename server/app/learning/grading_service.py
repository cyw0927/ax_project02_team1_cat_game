import logging
import uuid
from dataclasses import dataclass
from typing import Callable

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_sandbox_config
from app.battle.service import apply_battle_correct_result
from app.db.database import SessionLocal
from app.learning.models import Task, TaskAttempt, UserProficiency
from app.sandbox.executor import SandboxLimits
from app.sandbox.grader import TestExecutionResult, execute_test_cases
from app.users.models import User


logger = logging.getLogger(__name__)

STATUS_PENDING = "PENDING"
STATUS_RUNNING = "RUNNING"
STATUS_SUCCESS = "SUCCESS"
STATUS_FAILED = "FAILED"

FIRST_CORRECT_SOFT_REWARD = 100
HINT_FIRST_CORRECT_SOFT_REWARD = 50
FIRST_CORRECT_PROFICIENCY_GAIN = 10
HINT_FIRST_CORRECT_PROFICIENCY_GAIN = 5
MAX_PROFICIENCY_LEVEL = 100


@dataclass(frozen=True)
class ClaimedAttempt:
    submitted_code: str
    test_cases: str


SessionFactory = Callable[[], Session]
TestExecutor = Callable[..., TestExecutionResult]


def _commit(db: Session) -> None:
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise


def _claim_attempt(
    attempt_id: uuid.UUID,
    session_factory: SessionFactory,
) -> ClaimedAttempt | None:
    with session_factory() as db:
        attempt = db.get(TaskAttempt, attempt_id, with_for_update=True)
        if attempt is None or attempt.status != STATUS_PENDING:
            return None

        task = db.get(Task, attempt.task_id)
        if task is None:
            attempt.status = STATUS_FAILED
            attempt.is_correct = None
            _commit(db)
            return None

        attempt.status = STATUS_RUNNING
        attempt.is_correct = None
        claimed = ClaimedAttempt(
            submitted_code=attempt.submitted_code,
            test_cases=task.test_cases,
        )
        _commit(db)
        return claimed


def _apply_first_correct_reward(
    db: Session,
    *,
    attempt: TaskAttempt,
    user: User,
) -> None:
    task = db.get(Task, attempt.task_id)
    if task is None:
        raise RuntimeError("Task not found while applying learning reward")

    if attempt.used_hint:
        soft_reward = HINT_FIRST_CORRECT_SOFT_REWARD
        proficiency_gain = HINT_FIRST_CORRECT_PROFICIENCY_GAIN
    else:
        soft_reward = FIRST_CORRECT_SOFT_REWARD
        proficiency_gain = FIRST_CORRECT_PROFICIENCY_GAIN

    proficiency = db.scalar(
        select(UserProficiency)
        .where(
            UserProficiency.user_id == attempt.user_id,
            UserProficiency.concept_id == task.concept_id,
        )
        .with_for_update()
    )
    if proficiency is None:
        proficiency = UserProficiency(
            user_id=attempt.user_id,
            concept_id=task.concept_id,
            proficiency_level=0,
        )
        db.add(proficiency)

    user.soft_balance += soft_reward
    proficiency.proficiency_level = min(
        MAX_PROFICIENCY_LEVEL,
        proficiency.proficiency_level + proficiency_gain,
    )


def _finish_attempt(
    attempt_id: uuid.UUID,
    *,
    status: str,
    is_correct: bool | None,
    session_factory: SessionFactory,
) -> bool | None:
    with session_factory() as db:
        attempt = db.get(TaskAttempt, attempt_id, with_for_update=True)
        if attempt is None or attempt.status != STATUS_RUNNING:
            return None

        is_first_correct = False
        if status == STATUS_SUCCESS and is_correct is True:
            if attempt.context_type == "BATTLE":
                is_first_correct = apply_battle_correct_result(db, attempt)
            else:
                user = db.get(User, attempt.user_id, with_for_update=True)
                if user is None:
                    attempt.status = STATUS_FAILED
                    attempt.is_correct = None
                    _commit(db)
                    return None

                prior_correct_attempt_id = db.scalar(
                    select(TaskAttempt.id)
                    .where(
                        TaskAttempt.user_id == attempt.user_id,
                        TaskAttempt.task_id == attempt.task_id,
                        TaskAttempt.id != attempt.id,
                        TaskAttempt.status == STATUS_SUCCESS,
                        TaskAttempt.is_correct.is_(True),
                    )
                    .limit(1)
                )
                is_first_correct = prior_correct_attempt_id is None
                if is_first_correct:
                    _apply_first_correct_reward(db, attempt=attempt, user=user)

        attempt.status = status
        attempt.is_correct = is_correct
        _commit(db)
        return is_first_correct


def process_attempt_grading(
    attempt_id: uuid.UUID,
    *,
    session_factory: SessionFactory = SessionLocal,
    test_executor: TestExecutor = execute_test_cases,
) -> bool | None:
    claimed = _claim_attempt(attempt_id, session_factory)
    if claimed is None:
        return None

    try:
        config = get_sandbox_config()
        result = test_executor(
            claimed.submitted_code,
            claimed.test_cases,
            image=str(config["image"]),
            limits=SandboxLimits(
                timeout_seconds=float(config["timeout_seconds"]),
                memory=str(config["memory"]),
                cpus=str(config["cpus"]),
                output_bytes=int(config["output_bytes"]),
            ),
        )
    except Exception:
        logger.exception("Attempt grading failed", extra={"attempt_id": attempt_id})
        _finish_attempt(
            attempt_id,
            status=STATUS_FAILED,
            is_correct=None,
            session_factory=session_factory,
        )
        return None

    return _finish_attempt(
        attempt_id,
        status=STATUS_SUCCESS,
        is_correct=result.is_correct,
        session_factory=session_factory,
    )
