# 환경변수·설정값 분리 정책

이 문서는 코드 안에 직접 박아두면 안 되는 값과, 기획이 바뀔 수 있으므로 설정으로 분리하는 값의 기준을 정리한다.

---

## 1. 반드시 환경변수로 둘 값

예:

```text
DATABASE_URL
JWT_SECRET_KEY
외부 API KEY
Docker image 이름(환경별 차이가 있다면)
로그 레벨
서비스 타임존
```

실제 비밀값은 `.env`에 두고 Git에는 올리지 않는다.

`.env.example`에는 키 이름과 예시 형식만 둔다.

---

## 2. 코드에 박지 말아야 할 비즈니스 숫자

다음 값은 기획에서 바뀔 가능성이 높다.

```text
학습 보상량
출석 보상량
가챠 비용
가챠 확률
배틀 점수
승급전 제한시간
Docker timeout
동시 컨테이너 수
```

모든 값을 무조건 환경변수로 만들 필요는 없다.

원칙:

```text
보안/환경 의존 → 환경변수
기획 규칙 → config/constants 또는 DB 정책값
자주 운영에서 바꿔야 함 → DB/관리자 설정 검토
```

---

## 3. 추천 config 구조

예:

```python
class Settings:
    database_url: str
    timezone: str
    docker_image: str
    max_grading_concurrency: int
    grading_timeout_seconds: int
```

비즈니스 숫자는 별도의 domain config로 둘 수 있다.

```text
learning/reward rules
gacha rules
battle scoring rules
```

---

## 4. Docker 설정

현재 요구사항상 반드시 유지해야 하는 보안/자원 제한:

```text
memory = 128MB
CPU = 0.5
network = none
filesystem = read-only
```

이 값들은 단순 편의 설정이 아니라 안전 조건이므로 변경 시 이유를 문서화한다.

동시 실행 수 3~5, timeout, output cap 같은 값은 환경/테스트에 따라 조절 가능하도록 설정값으로 두는 편이 좋다.

---

## 5. 타임존

출석과 일일 제한을 위해 서비스 타임존을 한 곳에서 정의한다.

예:

```text
APP_TIMEZONE=Asia/Seoul
```

각 router가 제각각 `date.today()`를 호출하지 않도록 공통 함수/설정을 사용한다.

---

## 6. 개발/테스트/운영 분리

환경별 예:

```text
개발
DATABASE_URL=local postgres
LOG_LEVEL=DEBUG

테스트
별도 test database
Docker sandbox test image

운영
production database
LOG_LEVEL=INFO
```

서로 다른 환경이 같은 DB를 실수로 보지 않도록 한다.

---

## 7. `.env.example`

예시:

```env
DATABASE_URL=postgresql+psycopg://user:password@localhost:5432/cat_game
APP_TIMEZONE=Asia/Seoul
GRADING_DOCKER_IMAGE=cat-game-python-grader:latest
GRADING_MAX_CONCURRENCY=3
GRADING_TIMEOUT_SECONDS=5
JWT_SECRET_KEY=change-me
```

`JWT_SECRET_KEY=change-me`는 실제 운영값이 아니라 형식 설명용이다.

---

## 8. 금지

```text
password = "1234"
DATABASE_URL = "실제 비밀번호 포함 주소"
API_KEY = "실제 키"
```

같은 값을 repository에 commit하지 않는다.

---

## 9. 테스트

- `.env` 없이 필수 설정 누락 시 이해 가능한 오류
- `.env.example`만 보고 로컬 설정 가능
- 개발 DB와 테스트 DB 분리
- 잘못된 Docker image 이름일 때 SYSTEM_ERROR 처리
- timezone 설정 변경 시 출석 기준이 설정을 따르는지

---

# 결론

설정 분리의 목적은 파일을 복잡하게 만드는 것이 아니다.

```text
비밀값을 Git에서 분리
환경마다 달라지는 값 분리
자주 바뀌는 기획 숫자의 하드코딩 방지
```

이 세 가지가 핵심이다.