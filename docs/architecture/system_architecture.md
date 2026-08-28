# System Architecture

## 주요 구성

```text
Browser Prototype
  -> FastAPI
      -> PostgreSQL
      -> Docker Sandbox (grading)
```

- `prototype/`: 플레이어블 UI/게임 프로토타입
- `server/app/`: FastAPI 도메인 코드
- `server/alembic/`: DB migration
- `server/tests/`: API/샌드박스 테스트
- `scenario/`: 기능별 상세 설계 및 테스트 시나리오
- `docs/`: 프로젝트 전체 공통 문서와 운영 정책

## Backend domain

현재 백엔드는 이유가 함께 바뀌는 기능을 도메인 단위로 나눕니다.

- users
- learning
- battle
- ranking
- economy
- housing
- cats
- sandbox
- db
- core

`sandbox`는 비즈니스 도메인보다는 기술적 실행 경계이며, Python 제출 코드를 Docker에서 격리 실행하는 역할을 담당합니다.

## 핵심 원칙

- Docker 실행 중 DB transaction을 유지하지 않습니다.
- DB 명시적 lock은 꼭 필요한 상태 전이에만 사용합니다.
- API, UI, game state, cat movement 로직은 가능한 한 분리합니다.
- 확정되지 않은 비즈니스 규칙을 코드에 임의로 고정하지 않습니다.
