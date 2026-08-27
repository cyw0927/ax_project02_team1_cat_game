import os

from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL is not set. Create a server/.env file first.")

SANDBOX_IMAGE = os.getenv("SANDBOX_IMAGE")
SANDBOX_TIMEOUT_SECONDS = os.getenv("SANDBOX_TIMEOUT_SECONDS")
SANDBOX_MEMORY = os.getenv("SANDBOX_MEMORY")
SANDBOX_CPUS = os.getenv("SANDBOX_CPUS")
SANDBOX_OUTPUT_BYTES = os.getenv("SANDBOX_OUTPUT_BYTES")


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
    }
