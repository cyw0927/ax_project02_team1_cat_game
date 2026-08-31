from datetime import UTC, datetime

import pytest

from app.core.time import get_service_today


def test_service_today_uses_configured_timezone_before_midnight():
    now = datetime(2026, 8, 30, 14, 59, 59, tzinfo=UTC)

    assert get_service_today(now).isoformat() == "2026-08-30"


def test_service_today_changes_at_configured_timezone_midnight():
    now = datetime(2026, 8, 30, 15, 0, 0, tzinfo=UTC)

    assert get_service_today(now).isoformat() == "2026-08-31"


def test_service_today_rejects_naive_datetime():
    with pytest.raises(ValueError, match="timezone-aware"):
        get_service_today(datetime(2026, 8, 31, 0, 0, 0))
