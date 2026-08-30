FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    HOME=/tmp

RUN groupadd --system sandbox \
    && useradd --system --gid sandbox --no-create-home sandbox

WORKDIR /sandbox
USER sandbox:sandbox

CMD ["python", "-I", "-c", "print('sandbox ready')"]
