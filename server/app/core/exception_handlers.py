import logging

from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette import status
from starlette.exceptions import HTTPException

from app.core.schemas import ErrorDetail, ErrorInfo, ErrorResponse


logger = logging.getLogger(__name__)


STATUS_ERROR_CODES = {
    400: "BAD_REQUEST",
    401: "UNAUTHORIZED",
    403: "FORBIDDEN",
    404: "NOT_FOUND",
    405: "METHOD_NOT_ALLOWED",
    409: "CONFLICT",
    422: "VALIDATION_ERROR",
    500: "INTERNAL_SERVER_ERROR",
}


class AppException(Exception):
    """서비스에서 의도적으로 발생시키는 공통 예외."""

    def __init__(
        self,
        *,
        status_code: int,
        code: str,
        message: str,
        details: list[ErrorDetail] | None = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.message = message
        self.details = details or []


def create_error_response(
    *,
    status_code: int,
    code: str,
    message: str,
    details: list[ErrorDetail] | None = None,
) -> JSONResponse:
    """공통 오류 JSON 응답을 생성한다."""

    response = ErrorResponse(
        error=ErrorInfo(
            code=code,
            message=message,
            details=details or [],
        )
    )

    return JSONResponse(
        status_code=status_code,
        content=jsonable_encoder(response),
    )


async def app_exception_handler(
    request: Request,
    exc: AppException,
) -> JSONResponse:
    """AppException을 공통 오류 형식으로 변환한다."""

    return create_error_response(
        status_code=exc.status_code,
        code=exc.code,
        message=exc.message,
        details=exc.details,
    )


async def http_exception_handler(
    request: Request,
    exc: HTTPException,
) -> JSONResponse:
    """기존 HTTPException을 공통 오류 형식으로 변환한다."""

    code = STATUS_ERROR_CODES.get(exc.status_code, "HTTP_ERROR")
    message = exc.detail if isinstance(exc.detail, str) else "요청을 처리할 수 없습니다."

    return create_error_response(
        status_code=exc.status_code,
        code=code,
        message=message,
    )


async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    """요청값 검증 오류를 필드별 세부 정보로 변환한다."""

    details = [
        ErrorDetail(
            field=".".join(str(part) for part in error["loc"]),
            message=error["msg"],
            type=error["type"],
        )
        for error in exc.errors()
    ]

    return create_error_response(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        code="VALIDATION_ERROR",
        message="요청값이 올바르지 않습니다.",
        details=details,
    )


async def unexpected_exception_handler(
    request: Request,
    exc: Exception,
) -> JSONResponse:
    """처리되지 않은 예외의 내부 정보를 숨기고 공통 오류를 반환한다."""

    logger.error(
        "처리되지 않은 예외가 발생했습니다.",
        exc_info=(type(exc), exc, exc.__traceback__),
    )

    return create_error_response(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        code="INTERNAL_SERVER_ERROR",
        message="서버 내부 오류가 발생했습니다.",
    )


def register_exception_handlers(app: FastAPI) -> None:
    """FastAPI 애플리케이션에 공통 오류 처리기를 등록한다."""

    app.add_exception_handler(AppException, app_exception_handler)
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(
        RequestValidationError,
        validation_exception_handler,
    )
    app.add_exception_handler(Exception, unexpected_exception_handler)