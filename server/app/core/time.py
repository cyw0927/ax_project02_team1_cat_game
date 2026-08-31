from datetime import UTC, date, datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from app.core.config import APP_TIMEZONE


try:
    SERVICE_TIMEZONE = ZoneInfo(APP_TIMEZONE)
except ZoneInfoNotFoundError as exc:
    raise RuntimeError(
        f"APP_TIMEZONE must be a valid IANA timezone: {APP_TIMEZONE}"
    ) from exc


def get_service_today(now: datetime | None = None) -> date:
    """서비스 timezone을 기준으로 오늘 날짜를 반환한다."""

    current_time = now or datetime.now(UTC)

    if current_time.tzinfo is None:
        raise ValueError("now must be timezone-aware.")

    return current_time.astimezone(SERVICE_TIMEZONE).date()
