from fastapi import APIRouter, Depends, status
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.exception_handlers import AppException
from app.core.schemas import ErrorResponse, HealthResponse
from app.db.database import get_db


router = APIRouter(tags=["system"])


@router.get(
    "/health",
    response_model=HealthResponse,
    responses={
        status.HTTP_503_SERVICE_UNAVAILABLE: {
            "model": ErrorResponse,
            "description": "데이터베이스 연결 실패",
        }
    },
    summary="서버 상태 확인",
)
def health_check(
    db: Session = Depends(get_db),
) -> HealthResponse:
    """FastAPI 서버와 PostgreSQL 연결 상태를 확인한다."""

    try:
        db.execute(text("SELECT 1")).scalar_one()
    except SQLAlchemyError as exc:
        raise AppException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            code="DATABASE_UNAVAILABLE",
            message="데이터베이스에 연결할 수 없습니다.",
        ) from exc

    return HealthResponse(
        status="ok",
        database="connected",
    )