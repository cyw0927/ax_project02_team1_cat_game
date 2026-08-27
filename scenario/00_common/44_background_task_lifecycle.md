# BackgroundTask 채점 생명주기

이 문서는 일반 학습 코드 제출이 `202 Accepted`로 접수된 뒤 **FastAPI BackgroundTasks와 Docker 채점이 어떤 순서로 이어져야 하는지** 정리한다.

현재 작은 프로젝트에서는 Celery+Redis 같은 별도 큐를 바로 도입하기보다 FastAPI BackgroundTasks + 실행 동시성 제한으로 시작하는 방향을 우선한다.

---

## 1. 전체 흐름

```text
사용자 코드 제출
→ POST /attempts
→ TASK_ATTEMPTS PENDING INSERT
→ COMMIT
→ 202 Accepted 반환
→ BackgroundTask 실행
→ 실행 슬롯 대기
→ RUNNING 전환
→ Docker 채점
→ 최종 상태 계산
→ DB 저장
→ 컨테이너 정리
```

핵심은 **HTTP 요청과 Docker 실행을 같은 긴 요청으로 묶지 않는 것**이다.

---

## 2. 요청 단계

`POST /attempts`가 할 일:

1. 인증 사용자 확인
2. task 존재 확인
3. task 활성 상태 확인
4. submitted_code 형식 검증
5. `TASK_ATTEMPTS(status=PENDING)` 생성
6. commit
7. BackgroundTask 등록
8. `202 Accepted` 반환

응답 예:

```json
{
  "attempt_id": "attempt-uuid",
  "status": "PENDING"
}
```

202는 정답을 뜻하지 않는다.

---

## 3. 왜 먼저 commit하는가

BackgroundTask가 시작되기 전에 attempt row가 DB에 확실히 있어야 한다.

```text
PENDING 저장 안 됨
→ background worker가 attempt 조회
→ 찾을 수 없음
```

같은 순서 문제를 피한다.

따라서:

```text
attempt commit
→ background scheduling
```

순서를 지킨다.

---

## 4. BackgroundTask의 DB Session

요청 처리에 사용한 DB session은 Response 이후 닫힐 수 있다.

따라서 background 함수가 요청용 session 객체를 오래 붙잡고 사용하는 방식은 피하고, **background 작업 안에서 필요한 DB session을 새로 여는 구조**가 안전하다.

개념:

```text
HTTP request session
→ PENDING 저장 후 종료

BackgroundTask
→ 새 DB session 시작
→ attempt 조회/상태 변경
→ commit/rollback
→ session 종료
```

---

## 5. 실행 동시성 제한

30명이 동시에 제출해도 Docker 컨테이너를 무한 생성하면 안 된다.

현재 방향:

```text
동시에 실행 가능한 Docker 수 = 3~5 범위에서 설정
나머지 attempt = PENDING 상태로 실행 슬롯 대기
```

정확한 숫자는 설정값으로 관리하고 팀에서 확정한다.

Python `BoundedSemaphore` 같은 방식으로 한 프로세스 안의 동시 실행 수를 제한할 수 있다.

---

## 6. Semaphore의 중요한 한계

Semaphore가 Python 프로세스 안에 있으면:

```text
uvicorn worker 1 → 최대 3
uvicorn worker 2 → 최대 3
```

처럼 프로세스마다 따로 적용될 수 있다.

즉 Docker host 전체 최대 3개를 보장하는 것은 아니다.

MVP에서는:

```text
single worker
+ process-local semaphore
```

한계를 명확히 알고 사용하는 것이 단순하다.

멀티 worker가 필요해질 때 중앙 큐/공유 semaphore를 검토한다.

---

## 7. PENDING → RUNNING

실행 슬롯을 얻은 뒤 실제 Docker 실행 직전에 상태를 `RUNNING`으로 바꾸는 방식을 권장한다.

```text
PENDING
→ semaphore 획득
→ RUNNING 저장
→ Docker 실행
```

이렇게 하면 사용자에게:

```text
PENDING = 대기 중
RUNNING = 실제 채점 중
```

으로 설명할 수 있다.

정확한 status 목록은 팀 확정이 필요하다.

---

## 8. Docker 실행

확정된 자원 제한:

```text
memory = 128MB
CPU = 0.5
network = none
filesystem = read-only
```

추가 하드닝:

- capability drop
- no-new-privileges
- stdin/tty 비활성
- 출력 크기 제한
- 실행 timeout

정확한 timeout/output cap 값은 별도 결정한다.

---

## 9. 최종 상태 저장

Docker 결과를 분석해서 후보 상태 중 하나로 전환한다.

```text
PASSED
WRONG_ANSWER
RUNTIME_ERROR
TIMEOUT
SYSTEM_ERROR
```

필요하면:

```text
RUNNING → 최종상태
```

전환과 보상/숙련도 반영을 하나의 짧은 DB transaction으로 처리한다.

Docker 자체는 이 transaction 밖에서 이미 끝난 상태여야 한다.

---

## 10. 예외 처리

background 함수 전체에서 예외가 발생해도 attempt가 영원히 RUNNING에 남지 않도록 해야 한다.

예:

```text
Docker Engine 연결 실패
이미지 없음
컨테이너 생성 실패
서버 코드 예외
```

가능한 경우:

```text
attempt → SYSTEM_ERROR
```

로 기록한다.

프로세스 자체가 죽은 경우는 `37_failure_recovery_pending_stuck_policy.md`의 stale 정리 정책으로 처리한다.

---

## 11. 컨테이너 정리

성공/오답/timeout/예외와 관계없이 컨테이너 제거를 시도한다.

개념:

```text
try
  run grading
finally
  stop/remove container
```

컨테이너 cleanup 실패도 로그에 남긴다.

---

## 12. Polling과 연결

프론트는 제출 후 받은 attempt_id로 결과를 조회한다.

```text
POST /attempts
→ 202 + attempt_id
→ GET /attempts/{id}
→ PENDING/RUNNING이면 잠시 뒤 재조회
→ 최종상태면 polling 종료
```

정확한 polling 간격은 프론트와 조정한다.

---

## 13. 보상 지급 주의

정답 보상을 background task에서 처리할 경우 같은 문제의 여러 attempt가 동시에 PASSED가 될 수 있다.

따라서:

```text
정답 확인
→ 보상 자격 동시성 방어
→ 보상 지급
```

이 필요하다.

단순히 background worker마다 `이전 PASSED 없음`을 SELECT하는 것만으로는 충분하지 않을 수 있다.

---

## 14. BackgroundTasks의 한계

BackgroundTasks는 durable queue가 아니다.

서버 프로세스가 죽으면:

```text
PENDING은 DB에 있음
실행 예정 작업은 사라질 수 있음
```

따라서 현재 구조는:

```text
작은 MVP에 적합
하지만 작업 유실 가능성 존재
```

라고 명확히 문서화한다.

---

## 15. 언제 Celery/Redis 등을 검토할까

다음이 필요해지면 검토 가치가 커진다.

- 여러 API worker에서 동일한 중앙 큐 사용
- 서버 재시작 후에도 작업 보존
- 자동 retry
- 작업 우선순위
- worker 상태/모니터링
- 많은 동시 제출

현재 단계에서는 먼저 단순 구조를 안정적으로 구현하는 것이 우선이다.

---

## 16. 테스트

- PENDING 생성 후 202 즉시 반환
- 실행 슬롯을 초과한 제출은 PENDING 대기
- 슬롯 획득 후 RUNNING
- PASSED 저장
- WRONG_ANSWER 저장
- runtime error
- timeout
- Docker Engine failure → SYSTEM_ERROR
- 컨테이너 cleanup
- BackgroundTask가 별도 DB session을 사용
- 동시에 많은 제출에도 설정값 이상의 컨테이너가 한 프로세스에서 실행되지 않음
- 서버 재시작 후 stale PENDING 처리

---

# 결론

MVP 채점의 핵심 생명주기는 다음이다.

```text
요청은 짧게 접수
→ PENDING commit
→ 202 반환
→ BackgroundTask
→ 제한된 수의 Docker만 실행
→ 결과 DB 저장
→ polling으로 결과 확인
```

그리고 반드시 기억할 제한은:

```text
BackgroundTasks는 durable queue가 아님
process-local semaphore는 host 전체 제한이 아님
```

이다.