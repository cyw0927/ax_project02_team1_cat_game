import uuid
from collections.abc import Callable
from typing import Annotated

from fastapi import Depends, Header, status
from sqlalchemy.orm import Session

from app.core import config
from app.core.exception_handlers import AppException
from app.db.database import get_db
from app.users.models import User


CURRENT_USER_ID_HEADER = "X-User-ID"
DEVELOPMENT_IDENTITY_ENVIRONMENTS = {"development", "test"}
ROLE_USER = "USER"
ROLE_ADMIN = "ADMIN"
SUPPORTED_ROLES = frozenset({ROLE_USER, ROLE_ADMIN})


def get_current_user(
    x_user_id: Annotated[
        str | None,
        Header(alias=CURRENT_USER_ID_HEADER),
    ] = None,
    db: Session = Depends(get_db),
) -> User:
    """개발·테스트 환경에서 요청 헤더로 현재 사용자를 식별한다."""

    if config.APP_ENV.lower() not in DEVELOPMENT_IDENTITY_ENVIRONMENTS:
        raise AppException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            code="AUTHENTICATION_REQUIRED",
            message="인증이 필요합니다.",
        )

    if x_user_id is None:
        raise AppException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            code="CURRENT_USER_ID_REQUIRED",
            message=f"{CURRENT_USER_ID_HEADER} 헤더가 필요합니다.",
        )

    try:
        user_id = uuid.UUID(x_user_id)
    except ValueError as exc:
        raise AppException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            code="INVALID_CURRENT_USER_ID",
            message="현재 사용자 ID가 올바르지 않습니다.",
        ) from exc

    user = db.get(User, user_id)

    if user is None:
        raise AppException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            code="CURRENT_USER_NOT_FOUND",
            message="현재 사용자를 찾을 수 없습니다.",
        )

    return user


def require_roles(*allowed_roles: str) -> Callable[..., User]:
    """현재 사용자가 허용된 역할 중 하나인지 검사하는 dependency를 만든다."""

    normalized_roles = frozenset(role.upper() for role in allowed_roles)

    if not normalized_roles:
        raise ValueError("At least one allowed role is required.")

    unknown_roles = normalized_roles - SUPPORTED_ROLES
    if unknown_roles:
        unknown = ", ".join(sorted(unknown_roles))
        raise ValueError(f"Unsupported role(s): {unknown}")

    def role_guard(
        current_user: User = Depends(get_current_user),
    ) -> User:
        if current_user.role.upper() not in normalized_roles:
            raise AppException(
                status_code=status.HTTP_403_FORBIDDEN,
                code="INSUFFICIENT_ROLE",
                message="이 작업을 수행할 권한이 없습니다.",
            )

        return current_user

    return role_guard
