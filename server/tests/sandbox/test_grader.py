import json
import os

import pytest

from app.sandbox import grader
from app.sandbox.executor import SandboxLimits, SandboxResult


LIMITS = SandboxLimits(
    timeout_seconds=2,
    memory="128m",
    cpus="0.5",
    output_bytes=4096,
)


def sandbox_result(payload: dict) -> SandboxResult:
    return SandboxResult(
        exit_code=0,
        stdout=grader.RESULT_PREFIX + json.dumps(payload) + "\n",
        stderr="",
        timed_out=False,
        output_limited=False,
    )


def test_executes_all_configured_cases_and_parses_result(monkeypatch):
    captured = {}

    def fake_run(code, *, image, limits):
        captured.update(code=code, image=image, limits=limits)
        return sandbox_result(
            {"total_count": 3, "passed_count": 2, "failures": [
                {"index": 1, "reason": "WRONG_ANSWER"}
            ]}
        )

    monkeypatch.setattr(grader, "run_python_code", fake_run)

    result = grader.execute_test_cases(
        "def double_number(number):\n    return number * 2",
        json.dumps({
            "function_name": "double_number",
            "cases": [
                {"args": [3], "expected": 6},
                {"args": [0], "expected": 0},
                {"args": [-4], "expected": -8},
            ],
        }),
        image="cat-game-sandbox:local",
        limits=LIMITS,
    )

    assert result.total_count == 3
    assert result.passed_count == 2
    assert result.is_correct is False
    assert result.failures == ({"index": 1, "reason": "WRONG_ANSWER"},)
    assert captured["image"] == "cat-game-sandbox:local"
    assert captured["limits"] == LIMITS
    assert "double_number" in captured["code"]


@pytest.mark.parametrize(
    "test_cases",
    [
        "not-json",
        "[]",
        '{"function_name": "not-valid!", "cases": []}',
        '{"function_name": "answer", "cases": []}',
        '{"function_name": "answer", "cases": [{"args": 1, "expected": 1}]}',
        '{"function_name": "answer", "cases": [{"args": [], "expected": 1, "secret": true}]}',
    ],
)
def test_rejects_invalid_test_case_configuration(test_cases):
    with pytest.raises(grader.TestCaseConfigurationError):
        grader.build_test_runner_code("def answer(): return 1", test_cases)


@pytest.mark.parametrize(
    "result",
    [
        SandboxResult(1, "", "error", False, False),
        SandboxResult(137, "", "", True, False),
        SandboxResult(137, "", "", False, True),
    ],
)
def test_rejects_incomplete_sandbox_execution(monkeypatch, result):
    monkeypatch.setattr(grader, "run_python_code", lambda *args, **kwargs: result)

    with pytest.raises(grader.GradingResultError):
        grader.execute_test_cases(
            "def answer(): return 1",
            '{"function_name":"answer","cases":[{"args":[],"expected":1}]}',
            image="cat-game-sandbox:local",
            limits=LIMITS,
        )


def test_uses_last_marker_after_submission_output(monkeypatch):
    result = sandbox_result(
        {"total_count": 1, "passed_count": 1, "failures": []}
    )
    result = SandboxResult(
        exit_code=0,
        stdout="student output\n" + result.stdout,
        stderr="",
        timed_out=False,
        output_limited=False,
    )
    monkeypatch.setattr(grader, "run_python_code", lambda *args, **kwargs: result)

    execution = grader.execute_test_cases(
        "def answer(): return 1",
        '{"function_name":"answer","cases":[{"args":[],"expected":1}]}',
        image="cat-game-sandbox:local",
        limits=LIMITS,
    )

    assert execution.total_count == execution.passed_count == 1
    assert execution.is_correct is True


@pytest.mark.parametrize(
    "payload",
    [
        {"total_count": 0, "passed_count": 0, "failures": []},
        {"total_count": 1, "passed_count": 2, "failures": []},
        {"total_count": 1, "passed_count": -1, "failures": []},
        {"total_count": 2, "passed_count": 1, "failures": []},
        {"total_count": True, "passed_count": 1, "failures": []},
        {"total_count": 1, "passed_count": 0, "failures": ["invalid"]},
    ],
)
def test_rejects_inconsistent_sandbox_result(monkeypatch, payload):
    monkeypatch.setattr(
        grader,
        "run_python_code",
        lambda *args, **kwargs: sandbox_result(payload),
    )

    with pytest.raises(grader.GradingResultError):
        grader.execute_test_cases(
            "def answer(): return 1",
            '{"function_name":"answer","cases":[{"args":[],"expected":1}]}',
            image="cat-game-sandbox:local",
            limits=LIMITS,
        )


@pytest.mark.skipif(
    os.getenv("RUN_DOCKER_TESTS") != "1",
    reason="set RUN_DOCKER_TESTS=1 to run Docker integration tests",
)
def test_executes_seed_style_cases_in_real_docker_sandbox():
    execution = grader.execute_test_cases(
        "def double_number(number):\n    return number * 2",
        json.dumps({
            "function_name": "double_number",
            "cases": [
                {"args": [3], "expected": 6},
                {"args": [0], "expected": 0},
                {"args": [-4], "expected": -8},
            ],
        }),
        image="cat-game-sandbox:local",
        limits=LIMITS,
    )

    assert execution.total_count == 3
    assert execution.passed_count == 3
    assert execution.failures == ()
    assert execution.is_correct is True


@pytest.mark.skipif(
    os.getenv("RUN_DOCKER_TESTS") != "1",
    reason="set RUN_DOCKER_TESTS=1 to run Docker integration tests",
)
@pytest.mark.parametrize(
    ("submitted_code", "failure_reason"),
    [
        ("def answer(value): return value + 1", "WRONG_ANSWER"),
        ("def answer(value): raise RuntimeError('boom')", "RUNTIME_ERROR"),
        ("this is not valid Python", "SUBMISSION_ERROR"),
    ],
)
def test_marks_failed_submissions_in_real_docker_sandbox(
    submitted_code,
    failure_reason,
):
    execution = grader.execute_test_cases(
        submitted_code,
        '{"function_name":"answer","cases":[{"args":[1],"expected":1}]}',
        image="cat-game-sandbox:local",
        limits=LIMITS,
    )

    assert execution.is_correct is False
    assert execution.failures[0]["reason"] == failure_reason


@pytest.mark.skipif(
    os.getenv("RUN_DOCKER_TESTS") != "1",
    reason="set RUN_DOCKER_TESTS=1 to run Docker integration tests",
)
@pytest.mark.parametrize(
    ("submitted_code", "limits"),
    [
        (
            "def answer():\n    while True:\n        pass",
            SandboxLimits(0.2, "128m", "0.5", 4096),
        ),
        (
            "def answer():\n    print('x' * 10000)\n    return 1",
            SandboxLimits(2, "128m", "0.5", 256),
        ),
    ],
)
def test_rejects_timeout_and_output_limit_in_real_docker(
    submitted_code,
    limits,
):
    with pytest.raises(grader.GradingResultError):
        grader.execute_test_cases(
            submitted_code,
            '{"function_name":"answer","cases":[{"args":[],"expected":1}]}',
            image="cat-game-sandbox:local",
            limits=limits,
        )
