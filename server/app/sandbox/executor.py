import subprocess
import threading
import time
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
    output_limited: bool


class SandboxError(RuntimeError):
    pass


def _decode_output(data: bytes) -> str:
    return data.decode("utf-8", errors="replace")


def _kill_container(container_name: str) -> None:
    try:
        subprocess.run(
            ["docker", "kill", container_name],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=5,
            check=False,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass


def run_python_code(
    code: str,
    *,
    image: str,
    limits: SandboxLimits,
) -> SandboxResult:
    if limits.timeout_seconds <= 0:
        raise ValueError("timeout_seconds must be greater than 0")
    if limits.output_bytes <= 0:
        raise ValueError("output_bytes must be greater than 0")
    if not limits.memory:
        raise ValueError("memory must not be empty")
    if not limits.cpus:
        raise ValueError("cpus must not be empty")
    if not image:
        raise ValueError("image must not be empty")

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
        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
    except FileNotFoundError as exc:
        raise SandboxError("Docker CLI is not available") from exc

    stdout_buffer = bytearray()
    stderr_buffer = bytearray()
    output_lock = threading.Lock()
    output_limited = threading.Event()
    total_output = 0

    def read_stream(stream, target: bytearray) -> None:
        nonlocal total_output

        if stream is None:
            return

        try:
            while True:
                chunk = stream.read(4096)
                if not chunk:
                    break

                with output_lock:
                    remaining = limits.output_bytes - total_output
                    if remaining <= 0:
                        output_limited.set()
                        break

                    accepted = chunk[:remaining]
                    target.extend(accepted)
                    total_output += len(accepted)

                    if len(chunk) > remaining or total_output >= limits.output_bytes:
                        output_limited.set()
                        break
        finally:
            stream.close()

    stdout_thread = threading.Thread(
        target=read_stream,
        args=(process.stdout, stdout_buffer),
        daemon=True,
    )
    stderr_thread = threading.Thread(
        target=read_stream,
        args=(process.stderr, stderr_buffer),
        daemon=True,
    )
    stdout_thread.start()
    stderr_thread.start()

    deadline = time.monotonic() + limits.timeout_seconds
    timed_out = False

    while process.poll() is None:
        if output_limited.is_set():
            _kill_container(container_name)
            break

        if time.monotonic() >= deadline:
            timed_out = True
            _kill_container(container_name)
            break

        time.sleep(0.01)

    try:
        process.wait(timeout=1)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait()

    stdout_thread.join(timeout=1)
    stderr_thread.join(timeout=1)

    return SandboxResult(
        exit_code=process.returncode,
        stdout=_decode_output(bytes(stdout_buffer)),
        stderr=_decode_output(bytes(stderr_buffer)),
        timed_out=timed_out,
        output_limited=output_limited.is_set(),
    )
