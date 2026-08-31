import threading
import time
from concurrent.futures import ThreadPoolExecutor

from app.sandbox import executor


class FakeContainer:
    status = "running"

    def __init__(self, tracker):
        self.tracker = tracker

    def attach(self, **kwargs):
        return iter([])

    def reload(self):
        time.sleep(0.03)
        self.status = "exited"

    def wait(self):
        return {"StatusCode": 0}

    def remove(self, force):
        with self.tracker["lock"]:
            self.tracker["active"] -= 1


class FakeContainers:
    def __init__(self, tracker):
        self.tracker = tracker

    def run(self, **kwargs):
        with self.tracker["lock"]:
            self.tracker["active"] += 1
            self.tracker["maximum"] = max(
                self.tracker["maximum"], self.tracker["active"]
            )
            self.tracker["run_options"].append(kwargs)
        return FakeContainer(self.tracker)


class FakeClient:
    def __init__(self, tracker):
        self.containers = FakeContainers(tracker)

    def ping(self):
        return True

    def close(self):
        pass


def test_limits_concurrent_containers_and_applies_security_options(monkeypatch):
    tracker = {
        "active": 0,
        "maximum": 0,
        "lock": threading.Lock(),
        "run_options": [],
    }
    monkeypatch.setattr(executor.docker, "from_env", lambda: FakeClient(tracker))

    limits = executor.SandboxLimits(
        timeout_seconds=2,
        memory="128m",
        cpus="0.5",
        output_bytes=1024,
    )
    with ThreadPoolExecutor(max_workers=8) as pool:
        results = list(
            pool.map(
                lambda _: executor.run_python_code(
                    "print('ok')", image="python:3.12-slim", limits=limits
                ),
                range(8),
            )
        )

    assert tracker["maximum"] == 3
    assert all(result.exit_code == 0 for result in results)
    assert len(tracker["run_options"]) == 8
    for options in tracker["run_options"]:
        assert options["network_disabled"] is True
        assert options["mem_limit"] == "128m"
        assert options["nano_cpus"] == 500_000_000
        assert options["read_only"] is True
        assert options["cap_drop"] == ["ALL"]
        assert options["security_opt"] == ["no-new-privileges"]
        assert options["stdin_open"] is False
        assert options["tty"] is False


class TimeoutContainer(FakeContainer):
    def __init__(self, tracker):
        super().__init__(tracker)
        self.killed = False

    def reload(self):
        self.status = "running"

    def kill(self):
        self.killed = True
        self.status = "exited"
        self.tracker["killed"] = True

    def wait(self):
        return {"StatusCode": 137}


class TimeoutContainers(FakeContainers):
    def run(self, **kwargs):
        self.tracker["run_options"].append(kwargs)
        self.tracker["active"] += 1
        return TimeoutContainer(self.tracker)


class TimeoutClient(FakeClient):
    def __init__(self, tracker):
        self.containers = TimeoutContainers(tracker)


def test_kills_container_after_execution_timeout(monkeypatch):
    tracker = {
        "active": 0,
        "maximum": 0,
        "lock": threading.Lock(),
        "run_options": [],
        "killed": False,
    }
    monkeypatch.setattr(
        executor.docker,
        "from_env",
        lambda: TimeoutClient(tracker),
    )

    result = executor.run_python_code(
        "while True: pass",
        image="cat-game-sandbox:local",
        limits=executor.SandboxLimits(
            timeout_seconds=0.02,
            memory="128m",
            cpus="0.5",
            output_bytes=1024,
        ),
    )

    assert result.timed_out is True
    assert result.exit_code == 137
    assert tracker["killed"] is True

