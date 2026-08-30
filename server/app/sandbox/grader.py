import json
from dataclasses import dataclass
from typing import Any

from app.sandbox.executor import SandboxLimits, SandboxResult, run_python_code


RESULT_PREFIX = "__CAT_GAME_RESULT__="


class TestCaseConfigurationError(ValueError):
    pass


class GradingResultError(RuntimeError):
    pass


@dataclass(frozen=True)
class TestExecutionResult:
    total_count: int
    passed_count: int
    failures: tuple[dict[str, Any], ...]
    sandbox: SandboxResult

    @property
    def is_correct(self) -> bool:
        return (
            self.total_count > 0
            and self.passed_count == self.total_count
            and not self.failures
        )


def _parse_test_cases(test_cases: str) -> dict[str, Any]:
    try:
        payload = json.loads(test_cases)
    except (TypeError, json.JSONDecodeError) as exc:
        raise TestCaseConfigurationError(
            "test_cases must be valid JSON"
        ) from exc

    if not isinstance(payload, dict):
        raise TestCaseConfigurationError("test_cases must be a JSON object")

    function_name = payload.get("function_name")
    cases = payload.get("cases")

    if not isinstance(function_name, str) or not function_name.isidentifier():
        raise TestCaseConfigurationError(
            "function_name must be a valid Python identifier"
        )
    if not isinstance(cases, list) or not cases:
        raise TestCaseConfigurationError("cases must be a non-empty list")

    normalized_cases = []
    for index, case in enumerate(cases):
        if not isinstance(case, dict):
            raise TestCaseConfigurationError(
                f"case {index} must be a JSON object"
            )
        if set(case) != {"args", "expected"}:
            raise TestCaseConfigurationError(
                f"case {index} must contain only args and expected"
            )
        if not isinstance(case["args"], list):
            raise TestCaseConfigurationError(
                f"case {index} args must be a list"
            )
        normalized_cases.append(
            {"args": case["args"], "expected": case["expected"]}
        )

    return {
        "function_name": function_name,
        "cases": normalized_cases,
    }


def build_test_runner_code(submitted_code: str, test_cases: str) -> str:
    payload = _parse_test_cases(test_cases)
    submitted_json = json.dumps(submitted_code, ensure_ascii=False)
    payload_json = json.dumps(payload, ensure_ascii=False)

    return f"""\
import json as _json
import sys as _sys

_loads = _json.loads
_dumps = _json.dumps
_stdout = _sys.__stdout__
_source = _loads({submitted_json!r})
_spec = _loads({payload_json!r})
_namespace = {{"__name__": "__submission__"}}
_failures = []
_passed = 0

try:
    exec(compile(_source, "<submission>", "exec"), _namespace)
    _function = _namespace.get(_spec["function_name"])
    if not callable(_function):
        raise TypeError("required function is not callable")

    for _index, _case in enumerate(_spec["cases"]):
        try:
            _actual = _function(*_case["args"])
            if _actual == _case["expected"]:
                _passed += 1
            else:
                _failures.append({{"index": _index, "reason": "WRONG_ANSWER"}})
        except BaseException as _error:
            _failures.append({{
                "index": _index,
                "reason": "RUNTIME_ERROR",
                "error_type": type(_error).__name__,
            }})
except BaseException as _error:
    _failures = [{{
        "index": None,
        "reason": "SUBMISSION_ERROR",
        "error_type": type(_error).__name__,
    }}]

_result = {{
    "total_count": len(_spec["cases"]),
    "passed_count": _passed,
    "failures": _failures,
}}
_stdout.write({RESULT_PREFIX!r} + _dumps(_result, separators=(",", ":")) + "\\n")
"""


def _extract_result(
    sandbox: SandboxResult,
    *,
    expected_total: int,
) -> dict[str, Any]:
    marker_lines = [
        line.removeprefix(RESULT_PREFIX)
        for line in sandbox.stdout.splitlines()
        if line.startswith(RESULT_PREFIX)
    ]
    if not marker_lines:
        raise GradingResultError("sandbox did not return a grading result")

    try:
        result = json.loads(marker_lines[-1])
    except json.JSONDecodeError as exc:
        raise GradingResultError("sandbox returned invalid grading JSON") from exc

    if not isinstance(result, dict):
        raise GradingResultError("sandbox grading result must be an object")
    if type(result.get("total_count")) is not int:
        raise GradingResultError("sandbox result has invalid total_count")
    if type(result.get("passed_count")) is not int:
        raise GradingResultError("sandbox result has invalid passed_count")
    if not isinstance(result.get("failures"), list):
        raise GradingResultError("sandbox result has invalid failures")
    if result["total_count"] <= 0:
        raise GradingResultError("sandbox result total_count must be positive")
    if result["total_count"] != expected_total:
        raise GradingResultError("sandbox result has unexpected total_count")
    if not 0 <= result["passed_count"] <= result["total_count"]:
        raise GradingResultError("sandbox result has inconsistent counts")
    if not all(isinstance(failure, dict) for failure in result["failures"]):
        raise GradingResultError("sandbox result has invalid failure entries")

    return result


def execute_test_cases(
    submitted_code: str,
    test_cases: str,
    *,
    image: str,
    limits: SandboxLimits,
) -> TestExecutionResult:
    parsed_test_cases = _parse_test_cases(test_cases)
    runner_code = build_test_runner_code(submitted_code, test_cases)
    sandbox = run_python_code(runner_code, image=image, limits=limits)

    if sandbox.timed_out or sandbox.output_limited or sandbox.exit_code != 0:
        raise GradingResultError("sandbox execution did not complete normally")

    result = _extract_result(
        sandbox,
        expected_total=len(parsed_test_cases["cases"]),
    )
    return TestExecutionResult(
        total_count=result["total_count"],
        passed_count=result["passed_count"],
        failures=tuple(result["failures"]),
        sandbox=sandbox,
    )
