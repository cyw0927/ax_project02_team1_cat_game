import uuid
from datetime import datetime
from typing import Literal

from pydantic import ConfigDict, Field, model_validator

from app.core.schemas import SchemaBase


class ConceptResponse(SchemaBase):
    """학습 개념 목록 항목."""

    id: int
    name: str


class TaskSummaryResponse(SchemaBase):
    """개념별 문제 목록에서 공개하는 문제 요약."""

    id: uuid.UUID
    concept_id: int
    title: str
    type: str
    difficulty: str
    is_locked: bool = False


class TaskDetailResponse(TaskSummaryResponse):
    """코드 작성 화면에 공개하는 문제 상세."""

    description: str
    template_code: str


class TaskCatalogResponse(TaskSummaryResponse):
    """기존 전체 문제 목록 endpoint의 호환 응답."""

    template_code: str


class TaskHintResponse(SchemaBase):
    """힌트 버튼을 눌렀을 때 반환하는 사용 결과."""

    task_id: uuid.UUID
    hint_text: str
    used_hint: Literal[True] = True


class TaskAttemptCreateRequest(SchemaBase):
    """풀이 context를 포함한 코드 제출 요청."""

    model_config = ConfigDict(extra="forbid")

    task_id: uuid.UUID
    context_type: Literal["LEARNING", "DAILY", "BATTLE", "RANKING"]
    attendance_id: uuid.UUID | None = None
    room_task_id: uuid.UUID | None = None
    rank_challenge_task_id: uuid.UUID | None = None
    submitted_code: str = Field(min_length=1)
    used_hint: bool = False

    @model_validator(mode="after")
    def validate_context_ids(self):
        expected_ids = {
            "LEARNING": (None, None, None),
            "DAILY": (self.attendance_id, None, None),
            "BATTLE": (None, self.room_task_id, None),
            "RANKING": (None, None, self.rank_challenge_task_id),
        }
        actual_ids = (
            self.attendance_id,
            self.room_task_id,
            self.rank_challenge_task_id,
        )

        if self.context_type == "LEARNING":
            is_valid = actual_ids == expected_ids["LEARNING"]
        else:
            required_ids = expected_ids[self.context_type]
            is_valid = actual_ids == required_ids and any(actual_ids)

        if not is_valid:
            raise ValueError("context_type과 연결 ID 조합이 올바르지 않습니다.")

        if not self.submitted_code.strip():
            raise ValueError("submitted_code는 공백일 수 없습니다.")

        return self


class TaskAttemptAcceptedResponse(SchemaBase):
    """비동기 채점 대기열에 저장된 제출 응답."""

    attempt_id: uuid.UUID
    context_type: Literal["LEARNING", "DAILY", "BATTLE", "RANKING"]
    status: Literal["PENDING"]
    is_correct: None = None
    used_hint: bool
    attempted_at: datetime
