from pathlib import Path


DOCKERFILE = (
    Path(__file__).resolve().parents[2]
    / "sandbox"
    / "Dockerfile"
)


def test_sandbox_image_uses_minimal_python_and_non_root_user():
    content = DOCKERFILE.read_text(encoding="utf-8")

    assert "FROM python:3.12-slim" in content
    assert "USER sandbox:sandbox" in content
    assert "PYTHONDONTWRITEBYTECODE=1" in content
    assert "COPY " not in content
    assert "ADD " not in content


def test_sandbox_image_default_command_uses_isolated_python():
    content = DOCKERFILE.read_text(encoding="utf-8")

    assert 'CMD ["python", "-I", "-c"' in content
