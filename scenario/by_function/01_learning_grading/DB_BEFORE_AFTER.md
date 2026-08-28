# A. 학습·채점 DB Before / After

이 문서는 학습 API가 실행될 때 **DB가 실제로 어떻게 바뀌어야 하는지** 초보자도 확인할 수 있도록 정리한다.

중요:

- 현재 구현된 부분과 향후 채점 연결 후의 모습을 분리한다.
- 미정 보상량·숙련도 공식은 임의로 넣지 않는다.
- Docker 실행 자체는 긴 DB transaction 안에서 기다리지 않는다.

---

## A-DB01. 문제 목록 조회

### Before

`TASKS`

```text
T1  is_active=true
T2  is_active=false
```

### API

```http
GET /tasks
```

### After

DB 변화 없음.

Response에는 T1만 나오고 `test_cases`는 나오지 않는다.

---

## A-DB02. 정상 코드 제출 접수 — 현재 구현

### Before

`USERS`

```text
U1 존재
```

`TASKS`

```text
T1 is_active=true
```

`TASK_ATTEMPTS`

```text
없음
```

### 처리

```text
User 확인
→ active Task 확인
→ TASK_ATTEMPTS INSERT
→ COMMIT
```

### After

`TASK_ATTEMPTS`

```text
A1
user_id=U1
task_id=T1
submitted_code=사용자 코드
status=PENDING
is_correct=false   # 현재 모델/코드 기준
used_hint=요청값
attempted_at=서버 UTC 시각
```

HTTP는 `202 Accepted`.

### 중요한 의미

이 시점에는 아직 정답/오답 판정이 끝난 것이 아니다.

---

## A-DB03. 없는 사용자 또는 비활성 문제 제출

### Before

유효한 User 또는 active Task가 없음.

### 처리

검증 단계에서 중단.

### After

```text
TASK_ATTEMPTS 변화 없음
USERS 변화 없음
```

---

## A-DB04. BackgroundTask가 실제 채점을 시작하는 경우 — 향후

### Before

`TASK_ATTEMPTS`

```text
A1 status=PENDING
```

### 권장 처리

```text
BackgroundTask가 새 DB session 생성
→ A1 조회
→ 실행 slot 획득
→ RUNNING 상태를 사용하기로 했다면 짧게 UPDATE + COMMIT
→ DB transaction 종료
→ Docker 실행
```

### Docker 실행 중

DB transaction을 계속 열어두지 않는다.

### After 후보

```text
A1 status=RUNNING
```

`RUNNING`을 실제 상태로 사용할지는 팀 확정 대상이다.

---

## A-DB05. 정답 채점 완료 — 향후

### Before

```text
A1 status=PENDING 또는 RUNNING
```

Docker 결과는 정답.

### 처리 후보

```text
BEGIN
→ attempt 상태 재확인
→ A1 최종 상태 PASSED
→ is_correct=true
→ 보상 자격 확인
→ 필요한 USERS / USER_PROFICIENCY 변경
→ COMMIT
```

### After

최소:

```text
TASK_ATTEMPTS.A1.status = PASSED
TASK_ATTEMPTS.A1.is_correct = true
```

보상/숙련도 값은 확정 규칙이 있을 때만 변경한다.

---

## A-DB06. 오답

### Before

```text
A1 PENDING/RUNNING
```

### After 후보

```text
A1 status=WRONG_ANSWER
A1 is_correct=false
```

정답 보상은 없어야 한다.

오답도 attempt 이력 자체는 남긴다.

---

## A-DB07. Runtime Error

사용자 코드가 실행 중 오류를 낸다.

### After 후보

```text
A1 status=RUNTIME_ERROR
A1 is_correct=false
```

사용자 코드 오류와 서버 `SYSTEM_ERROR`는 구분한다.

오류 메시지를 나중에도 보여주기로 확정하면 `result_message` 같은 스키마 확장을 검토한다.

---

## A-DB08. Timeout

### Before

```text
A1 PENDING/RUNNING
```

### Docker

실행 제한시간을 초과하여 컨테이너 종료.

### After 후보

```text
A1 status=TIMEOUT
A1 is_correct=false
```

컨테이너는 제거되어야 한다.

DB에는 사용자 보상 증가가 없어야 한다.

---

## A-DB09. Docker/System Error

예:

```text
Docker Engine 연결 실패
이미지 없음
서버 내부 예외
```

### After 후보

```text
A1 status=SYSTEM_ERROR
```

보상/숙련도를 잘못 반영하지 않는다.

프로세스 자체가 죽어 update를 못 했다면 stale PENDING/RUNNING 복구 정책 대상이다.

---

## A-DB10. 같은 문제 재제출

### Before

```text
A1: U1/T1 과거 attempt
```

### 새 제출

새 row를 만든다.

### After

```text
A1: 과거 attempt 유지
A2: 새로운 attempt 생성
```

기존 row를 덮어쓰지 않는다.

이 구조 덕분에 재시도 이력을 볼 수 있다.

---

## A-DB11. 최초 정답 보상 경쟁

### 위험한 Before

같은 사용자/문제의 두 attempt가 거의 동시에 정답으로 끝난다.

```text
A10 PASSED 처리 직전
A11 PASSED 처리 직전
과거 확정 PASSED 없음
```

### 잘못된 구현

```text
A10: 이전 PASSED 없음 SELECT
A11: 이전 PASSED 없음 SELECT
→ 둘 다 보상 지급
```

### 올바른 After 목표

확정된 보상 횟수가 1회라면:

```text
A10/A11 둘 다 정답 이력은 남을 수 있음
하지만 USERS 재화 증가는 1회만
```

이를 위해 lock/상태 flag/유일성 등 실제 DB 방어 구조를 먼저 확정한다.

---

## A-DB12. 채점 최종 저장 실패

### 상황

Docker 채점은 끝났지만 DB 최종 UPDATE가 실패.

### 처리

```text
ROLLBACK
→ 부분적인 보상/숙련도만 저장되면 안 됨
```

다시 처리할 수 있도록 로그와 attempt 상태를 안전하게 정리한다.

---

# 한눈에 보는 핵심

```text
POST /attempts
Before: attempt 없음
After:  PENDING row 생성

BackgroundTask
PENDING → (RUNNING) → 최종 상태

Docker
DB transaction 밖에서 실행

최종 저장
상태 + 보상/숙련도처럼 함께 성공해야 하는 값만 짧은 transaction
```

학습 DB의 핵심은 **모든 제출을 이력으로 남기면서, 긴 Docker 실행과 DB transaction을 분리하고, 정답 보상은 중복되지 않게 하는 것**이다.
