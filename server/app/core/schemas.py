from pydantic import BaseModel, ConfigDict, Field


class SchemaBase(BaseModel):
    """프로젝트의 모든 요청·응답 스키마가 공통으로 상속하는 기본 클래스."""

    model_config = ConfigDict(from_attributes=True)


class MessageResponse(SchemaBase):
    """간단한 처리 결과 메시지 응답."""

    message: str


class ErrorDetail(SchemaBase):
    """입력값 오류 등 세부 오류 정보."""

    field: str | None = None
    message: str
    type: str | None = None


class ErrorInfo(SchemaBase):
    """오류 코드와 사용자에게 전달할 메시지."""

    code: str
    message: str
    details: list[ErrorDetail] = Field(default_factory=list)


class ErrorResponse(SchemaBase):
    """모든 API에서 사용하는 공통 오류 응답."""

    error: ErrorInfo


class HealthResponse(SchemaBase):
    """서버와 데이터베이스 상태 응답."""

    status: str
    database: str