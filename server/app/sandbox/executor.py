import threading
import time
import uuid
from dataclasses import dataclass

import docker
from docker.errors import APIError, DockerException, NotFound


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


def _kill_container(container) -> None:
    try:
        container.kill()
    except (APIError, NotFound):
        pass


def _remove_container(container) -> None:
    try:
        container.remove(force=True)
    except (APIError, NotFound):
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

    try:
        cpu_count = float(limits.cpus)
    except ValueError as exc:
        raise ValueError("cpus must be a number") from exc

    if cpu_count <= 0:
        raise ValueError("cpus must be greater than 0")

    nano_cpus = int(cpu_count * 1_000_000_000)
    container_name = f"cat-game-sandbox-{uuid.uuid4().hex}"
    client = docker.from_env()
    container = None

    stdout_buffer = bytearray()
    stderr_buffer = bytearray()
    output_lock = threading.Lock()
    output_limited = threading.Event()
    total_output = 0

    def append_output(data: bytes, target: bytearray) -> None:
        nonlocal total_output

        if not data:
            return

        with output_lock:
            remaining = limits.output_bytes - total_output
            if remaining <= 0:
                output_limited.set()
                return

            accepted = data[:remaining]
            target.extend(accepted)
            total_output += len(accepted)

            if len(data) > remaining or total_output >= limits.output_bytes:
                output_limited.set()

    def read_logs() -> None:
        if container is None:
            return

        try:
            stream = container.attach(
                stream=True,
                logs=True,
                stdout=True,
                stderr=True,
                demux=True,
            )
            for stdout_chunk, stderr_chunk in stream:
                if stdout_chunk:
                    append_output(stdout_chunk, stdout_buffer)
                if stderr_chunk:
                    append_output(stderr_chunk, stderr_buffer)
                if output_limited.is_set():
                    break
        except (APIError, DockerException):
            return

    try:
        try:
            container = client.containers.run(
                image=image,
                command=["python", "-I", "-c", code],
                name=container_name,
                detach=True,
                network_disabled=True,
                mem_limit=limits.memory,
                nano_cpus=nano_cpus,
                read_only=True,
                cap_drop=["ALL"],
                security_opt=["no-new-privileges"],
                stdin_open=False,
                tty=False,
            )
        except (APIError, DockerException) as exc:
            raise SandboxError("Docker sandbox could not be started") from exc

        log_thread = threading.Thread(target=read_logs, daemon=True)
        log_thread.start()

        deadline = time.monotonic() + limits.timeout_seconds
        timed_out = False

        while True:
            if output_limited.is_set():
                _kill_container(container)
                break

            if time.monotonic() >= deadline:
                timed_out = True
                _kill_container(container)
                break

            try:
                container.reload()
            except (APIError, NotFound) as exc:
                raise SandboxError("Docker sandbox status could not be read") from exc

            if container.status in {"exited", "dead"}:
                break

            time.sleep(0.01)

        try:
            wait_result = container.wait()
            exit_code = wait_result.get("StatusCode")
        except (APIError, NotFound) as exc:
            raise SandboxError("Docker sandbox result could not be read") from exc

        log_thread.join(timeout=1)

        return SandboxResult(
            exit_code=exit_code,
            stdout=_decode_output(bytes(stdout_buffer)),
            stderr=_decode_output(bytes(stderr_buffer)),
            timed_out=timed_out,
            output_limited=output_limited.is_set(),
        )
    finally:
        if container is not None:
            _remove_container(container)
        client.close()
