import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.exception_handlers import AppException
from app.core.schemas import ErrorResponse
from app.battle.models import RoomParticipant, RoomTask
from app.db.database import get_db
from app.learning.models import Concept, Task, TaskAttempt, UserProficiency
from app.learning.schemas import (
    ConceptResponse,
    TaskCatalogResponse,
    TaskDetailResponse,
    TaskHintResponse,
    TaskAttemptAcceptedResponse,
    TaskAttemptCreateRequest,
    TaskSummaryResponse,
)
from app.ranking.models import RankChallenge, RankChallengeTask
from app.users.dependencies import ROLE_ADMIN, ROLE_USER, require_roles
from app.users.models import Attendance, User

router = APIRouter(tags=["learning"])


@router.get(
    "/concepts",
    response_model=list[ConceptResponse],
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
    summary="학습 개념 목록 조회",
)
def get_concepts(
    _: User = Depends(require_roles(ROLE_USER, ROLE_ADMIN)),
    db: Session = Depends(get_db),
) -> list[ConceptResponse]:
    concepts = db.scalars(select(Concept).order_by(Concept.id)).all()

    return [
        ConceptResponse.model_validate(concept)
        for concept in concepts
    ]


@router.get(
    "/concepts/{concept_id}/tasks",
    response_model=list[TaskSummaryResponse],
    responses={
        status.HTTP_401_UNAUTHORIZED: {
            "model": ErrorResponse,
            "description": "현재 사용자 식별 실패",
        },
        status.HTTP_403_FORBIDDEN: {
            "model": ErrorResponse,
            "description": "허용되지 않은 사용자 역할",
        },
        status.HTTP_404_NOT_FOUND: {
            "model": ErrorResponse,
            "description": "개념을 찾을 수 없음",
        },
    },
    summary="개념별 문제 목록 조회",
)
def get_concept_tasks(
    concept_id: int,
    _: User = Depends(require_roles(ROLE_USER, ROLE_ADMIN)),
    db: Session = Depends(get_db),
) -> list[TaskSummaryResponse]:
    if db.get(Concept, concept_id) is None:
        raise AppException(
            status_code=status.HTTP_404_NOT_FOUND,
            code="CONCEPT_NOT_FOUND",
            message="개념을 찾을 수 없습니다.",
        )

    tasks = db.scalars(
        select(Task)
        .where(
            Task.concept_id == concept_id,
            Task.is_active.is_(True),
        )
        .order_by(Task.id)
    ).all()

    return [TaskSummaryResponse.model_validate(task) for task in tasks]


@router.get(
    "/tasks/{task_id}",
    response_model=TaskDetailResponse,
    responses={
        status.HTTP_401_UNAUTHORIZED: {
            "model": ErrorResponse,
            "description": "현재 사용자 식별 실패",
        },
        status.HTTP_403_FORBIDDEN: {
            "model": ErrorResponse,
            "description": "허용되지 않은 사용자 역할",
        },
        status.HTTP_404_NOT_FOUND: {
            "model": ErrorResponse,
            "description": "활성 문제를 찾을 수 없음",
        },
    },
    summary="문제 상세 조회",
)
def get_task_detail(
    task_id: uuid.UUID,
    _: User = Depends(require_roles(ROLE_USER, ROLE_ADMIN)),
    db: Session = Depends(get_db),
) -> TaskDetailResponse:
    task = db.scalar(
        select(Task).where(
            Task.id == task_id,
            Task.is_active.is_(True),
        )
    )

    if task is None:
        raise AppException(
            status_code=status.HTTP_404_NOT_FOUND,
            code="TASK_NOT_FOUND",
            message="문제를 찾을 수 없습니다.",
        )

    return TaskDetailResponse.model_validate(task)


@router.post(
    "/tasks/{task_id}/hint",
    response_model=TaskHintResponse,
    responses={
        status.HTTP_401_UNAUTHORIZED: {
            "model": ErrorResponse,
            "description": "현재 사용자 식별 실패",
        },
        status.HTTP_403_FORBIDDEN: {
            "model": ErrorResponse,
            "description": "허용되지 않은 사용자 역할",
        },
        status.HTTP_404_NOT_FOUND: {
            "model": ErrorResponse,
            "description": "활성 문제 또는 힌트를 찾을 수 없음",
        },
    },
    summary="문제 힌트 조회 및 사용",
)
def use_task_hint(
    task_id: uuid.UUID,
    _: User = Depends(require_roles(ROLE_USER, ROLE_ADMIN)),
    db: Session = Depends(get_db),
) -> TaskHintResponse:
    task = db.scalar(
        select(Task).where(
            Task.id == task_id,
            Task.is_active.is_(True),
        )
    )

    if task is None:
        raise AppException(
            status_code=status.HTTP_404_NOT_FOUND,
            code="TASK_NOT_FOUND",
            message="문제를 찾을 수 없습니다.",
        )

    if task.hint_text is None:
        raise AppException(
            status_code=status.HTTP_404_NOT_FOUND,
            code="HINT_NOT_AVAILABLE",
            message="사용 가능한 힌트가 없습니다.",
        )

    return TaskHintResponse(
        task_id=task.id,
        hint_text=task.hint_text,
        used_hint=True,
    )


@router.get(
    "/tasks",
    response_model=list[TaskCatalogResponse],
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
    deprecated=True,
    summary="전체 활성 문제 목록 조회(호환용)",
)
def get_tasks(
    _: User = Depends(require_roles(ROLE_USER, ROLE_ADMIN)),
    db: Session = Depends(get_db),
) -> list[TaskCatalogResponse]:
    tasks = db.scalars(
        select(Task)
        .where(Task.is_active.is_(True))
        .order_by(Task.id)
    ).all()

    return [
        TaskCatalogResponse.model_validate(task)
        for task in tasks
    ]


@router.get("/users/{user_id}/proficiency")
def get_user_proficiency(
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
            Concept.id,
            Concept.name,
            UserProficiency.proficiency_level,
        )
        .join(UserProficiency, UserProficiency.concept_id == Concept.id)
        .where(UserProficiency.user_id == user_id)
        .order_by(Concept.id)
    ).all()

    return [
        {
            "concept_id": concept_id,
            "concept_name": concept_name,
            "proficiency_level": proficiency_level,
        }
        for concept_id, concept_name, proficiency_level in rows
    ]


@router.get("/users/{user_id}/attempts")
def get_user_attempts(
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
            TaskAttempt.id,
            TaskAttempt.task_id,
            Task.concept_id,
            Task.type,
            Task.difficulty,
            TaskAttempt.status,
            TaskAttempt.is_correct,
            TaskAttempt.used_hint,
            TaskAttempt.attempted_at,
        )
        .join(Task, Task.id == TaskAttempt.task_id)
        .where(TaskAttempt.user_id == user_id)
        .order_by(TaskAttempt.attempted_at.desc())
    ).all()

    return [
        {
            "attempt_id": attempt_id,
            "task_id": task_id,
            "concept_id": concept_id,
            "type": task_type,
            "difficulty": difficulty,
            "status": attempt_status,
            "is_correct": is_correct,
            "used_hint": used_hint,
            "attempted_at": attempted_at,
        }
        for (
            attempt_id,
            task_id,
            concept_id,
            task_type,
            difficulty,
            attempt_status,
            is_correct,
            used_hint,
            attempted_at,
        ) in rows
    ]


@router.get("/attempts/{attempt_id}")
def get_attempt_result(
    attempt_id: uuid.UUID,
    db: Session = Depends(get_db),
):
    row = db.execute(
        select(
            TaskAttempt.id,
            TaskAttempt.task_id,
            Task.concept_id,
            Task.type,
            Task.difficulty,
            TaskAttempt.status,
            TaskAttempt.is_correct,
            TaskAttempt.used_hint,
            TaskAttempt.attempted_at,
        )
        .join(Task, Task.id == TaskAttempt.task_id)
        .where(TaskAttempt.id == attempt_id)
    ).one_or_none()

    if row is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Attempt not found",
        )

    (
        found_attempt_id,
        task_id,
        concept_id,
        task_type,
        difficulty,
        attempt_status,
        is_correct,
        used_hint,
        attempted_at,
    ) = row

    return {
        "attempt_id": found_attempt_id,
        "task_id": task_id,
        "concept_id": concept_id,
        "type": task_type,
        "difficulty": difficulty,
        "status": attempt_status,
        "is_correct": is_correct,
        "used_hint": used_hint,
        "attempted_at": attempted_at,
    }


@router.post(
    "/attempts",
    response_model=TaskAttemptAcceptedResponse,
    status_code=status.HTTP_202_ACCEPTED,
    responses={
        status.HTTP_401_UNAUTHORIZED: {
            "model": ErrorResponse,
            "description": "현재 사용자 식별 실패",
        },
        status.HTTP_403_FORBIDDEN: {
            "model": ErrorResponse,
            "description": "허용되지 않은 사용자 역할",
        },
        status.HTTP_404_NOT_FOUND: {
            "model": ErrorResponse,
            "description": "활성 문제 또는 풀이 context를 찾을 수 없음",
        },
        status.HTTP_422_UNPROCESSABLE_CONTENT: {
            "model": ErrorResponse,
            "description": "제출 요청값 검증 실패",
        },
    },
    summary="코드 제출 접수",
)
def submit_attempt(
    payload: TaskAttemptCreateRequest,
    current_user: User = Depends(require_roles(ROLE_USER, ROLE_ADMIN)),
    db: Session = Depends(get_db),
) -> TaskAttemptAcceptedResponse:
    task = db.scalar(
        select(Task).where(
            Task.id == payload.task_id,
            Task.is_active.is_(True),
        )
    )

    if task is None:
        raise AppException(
            status_code=status.HTTP_404_NOT_FOUND,
            code="TASK_NOT_FOUND",
            message="문제를 찾을 수 없습니다.",
        )

    if not _attempt_context_exists(payload, current_user.id, db):
        raise AppException(
            status_code=status.HTTP_404_NOT_FOUND,
            code="ATTEMPT_CONTEXT_NOT_FOUND",
            message="풀이 context를 찾을 수 없습니다.",
        )

    attempt = TaskAttempt(
        user_id=current_user.id,
        task_id=payload.task_id,
        context_type=payload.context_type,
        attendance_id=payload.attendance_id,
        room_task_id=payload.room_task_id,
        rank_challenge_task_id=payload.rank_challenge_task_id,
        submitted_code=payload.submitted_code,
        status="PENDING",
        is_correct=None,
        used_hint=payload.used_hint,
        attempted_at=datetime.now(timezone.utc),
    )
    db.add(attempt)

    try:
        db.commit()
    except Exception:
        db.rollback()
        raise

    db.refresh(attempt)

    return TaskAttemptAcceptedResponse(
        attempt_id=attempt.id,
        context_type=attempt.context_type,
        status=attempt.status,
        is_correct=attempt.is_correct,
        used_hint=attempt.used_hint,
        attempted_at=attempt.attempted_at,
    )


def _attempt_context_exists(
    payload: TaskAttemptCreateRequest,
    user_id: uuid.UUID,
    db: Session,
) -> bool:
    if payload.context_type == "LEARNING":
        return True

    if payload.context_type == "DAILY":
        context_id = db.scalar(
            select(Attendance.id).where(
                Attendance.id == payload.attendance_id,
                Attendance.user_id == user_id,
                Attendance.daily_task_ids.contains([str(payload.task_id)]),
            )
        )
    elif payload.context_type == "BATTLE":
        context_id = db.scalar(
            select(RoomTask.id)
            .join(
                RoomParticipant,
                RoomParticipant.room_id == RoomTask.room_id,
            )
            .where(
                RoomTask.id == payload.room_task_id,
                RoomTask.task_id == payload.task_id,
                RoomParticipant.user_id == user_id,
            )
        )
    else:
        context_id = db.scalar(
            select(RankChallengeTask.id)
            .join(
                RankChallenge,
                RankChallenge.id == RankChallengeTask.challenge_id,
            )
            .where(
                RankChallengeTask.id == payload.rank_challenge_task_id,
                RankChallengeTask.task_id == payload.task_id,
                RankChallenge.user_id == user_id,
            )
        )

    return context_id is not None
