import os

from dotenv import load_dotenv

load_dotenv()

APP_ENV = os.getenv("APP_ENV", "development")
APP_HOST = os.getenv("APP_HOST", "127.0.0.1")
APP_TIMEZONE = os.getenv("APP_TIMEZONE", "Asia/Seoul")

try:
    APP_PORT = int(os.getenv("APP_PORT", "8000"))
except ValueError as exc:
    raise RuntimeError("APP_PORT must be an integer.") from exc

CORS_ORIGINS = [
    origin.strip().rstrip("/")
    for origin in os.getenv(
        "CORS_ORIGINS",
        "http://localhost:5500,http://127.0.0.1:5500",
    ).split(",")
    if origin.strip()
]

if not CORS_ORIGINS:
    raise RuntimeError("CORS_ORIGINS must contain at least one origin.")

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL is not set. Create a server/.env file first.")

SANDBOX_IMAGE = os.getenv("SANDBOX_IMAGE")
SANDBOX_TIMEOUT_SECONDS = os.getenv("SANDBOX_TIMEOUT_SECONDS")
SANDBOX_MEMORY = os.getenv("SANDBOX_MEMORY", "128m")
SANDBOX_CPUS = os.getenv("SANDBOX_CPUS", "0.5")
SANDBOX_OUTPUT_BYTES = os.getenv("SANDBOX_OUTPUT_BYTES")
SANDBOX_MAX_CONCURRENCY = os.getenv("SANDBOX_MAX_CONCURRENCY", "3")


def get_sandbox_max_concurrency() -> int:
    try:
        max_concurrency = int(SANDBOX_MAX_CONCURRENCY)
    except (TypeError, ValueError) as exc:
        raise RuntimeError(
            "SANDBOX_MAX_CONCURRENCY must be an integer."
        ) from exc

    if max_concurrency <= 0:
        raise RuntimeError(
            "SANDBOX_MAX_CONCURRENCY must be greater than 0."
        )

    return max_concurrency


def get_sandbox_config() -> dict[str, str | float | int]:
    values = {
        "SANDBOX_IMAGE": SANDBOX_IMAGE,
        "SANDBOX_TIMEOUT_SECONDS": SANDBOX_TIMEOUT_SECONDS,
        "SANDBOX_MEMORY": SANDBOX_MEMORY,
        "SANDBOX_CPUS": SANDBOX_CPUS,
        "SANDBOX_OUTPUT_BYTES": SANDBOX_OUTPUT_BYTES,
    }
    missing = [name for name, value in values.items() if not value]

    if missing:
        raise RuntimeError(
            "Missing sandbox settings: " + ", ".join(missing)
        )

    try:
        timeout_seconds = float(SANDBOX_TIMEOUT_SECONDS)
        output_bytes = int(SANDBOX_OUTPUT_BYTES)
    except (TypeError, ValueError) as exc:
        raise RuntimeError(
            "SANDBOX_TIMEOUT_SECONDS must be a number and "
            "SANDBOX_OUTPUT_BYTES must be an integer."
        ) from exc

    return {
        "image": SANDBOX_IMAGE,
        "timeout_seconds": timeout_seconds,
        "memory": SANDBOX_MEMORY,
        "cpus": SANDBOX_CPUS,
        "output_bytes": output_bytes,
        "max_concurrency": get_sandbox_max_concurrency(),
    }
