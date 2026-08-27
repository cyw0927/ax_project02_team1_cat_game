import subprocess
import uuid
from dataclasses import dataclass


@dataclass(frozen=True)
class SandboxLimits:
    timeout_seconds: float
    memory: str
    cpus: str
    output_bytes: int


@dataclass(frozen=True)
class SandboxResult:
    exit_code: int | None
    stdout: str
    stderr: str
    timed_out: bool


class SandboxError(RuntimeError):
    pass


def _decode_output(data: bytes | str | None, limit: int) -> str:
    if data is None:
        return ""

    if isinstance(data, str):
        data = data.encode("utf-8", errors="replace")

    return data[:limit].decode("utf-8", errors="replace")


def run_python_code(
    code: str,
    *,
    image: str,
    limits: SandboxLimits,
) -> SandboxResult:
    container_name = f"cat-game-sandbox-{uuid.uuid4().hex}"
    command = [
        "docker",
        "run",
        "--rm",
        "--name",
        container_name,
        "--network",
        "none",
        "--memory",
        limits.memory,
        "--cpus",
        limits.cpus,
        "--read-only",
        "--cap-drop",
        "ALL",
        "--security-opt",
        "no-new-privileges",
        image,
        "python",
        "-I",
        "-c",
        code,
    ]

    try:
        completed = subprocess.run(
            command,
            capture_output=True,
            timeout=limits.timeout_seconds,
            check=False,
        )
    except FileNotFoundError as exc:
        raise SandboxError("Docker CLI is not available") from exc
    except subprocess.TimeoutExpired as exc:
        subprocess.run(
            ["docker", "kill", container_name],
            capture_output=True,
            check=False,
        )
        return SandboxResult(
            exit_code=None,
            stdout=_decode_output(exc.stdout, limits.output_bytes),
            stderr=_decode_output(exc.stderr, limits.output_bytes),
            timed_out=True,
        )

    return SandboxResult(
        exit_code=completed.returncode,
        stdout=_decode_output(completed.stdout, limits.output_bytes),
        stderr=_decode_output(completed.stderr, limits.output_bytes),
        timed_out=False,
    )
