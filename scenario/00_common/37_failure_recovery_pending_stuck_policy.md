# 장애 복구·PENDING 고착 처리 정책

이 문서는 서버가 중간에 죽거나 Docker 채점이 실패했을 때 `PENDING`/`RUNNING` 상태가 영원히 남는 문제를 어떻게 다룰지 정리한다.

## 1. 왜 필요한가

현재 일반 학습 제출 흐름은:

```text
POST /attempts
→ TASK_ATTEMPTS PENDING 저장
→ 202 반환
→ BackgroundTask에서 Docker 채점
```

이다.

문제는 PENDING을 저장한 뒤 서버 프로세스가 종료될 수 있다는 점이다.

```text
DB에는 PENDING
하지만 실제 작업은 사라짐
```

이 상태를 방치하면 프론트가 계속 채점 중이라고 표시할 수 있다.

## 2. BackgroundTasks의 한계

FastAPI BackgroundTasks는 작은 MVP에서 단순하고 좋지만 영속적인 작업 큐가 아니다.

서버 재시작/프로세스 종료 시 실행 중이거나 대기 중이던 작업을 복구해 주지 않는다.

따라서 현재 구조에서는 이 한계를 문서화하고 복구 기준을 정한다.

## 3. PENDING과 RUNNING 구분

추천 상태 의미:

```text
PENDING = 접수됐지만 아직 실행 슬롯을 못 얻음
RUNNING = Docker 채점 실제 시작
```

최종 상태:

```text
PASSED
WRONG_ANSWER
RUNTIME_ERROR
TIMEOUT
SYSTEM_ERROR
```

정확한 상태 목록은 P0 결정사항으로 확정한다.

## 4. 고착 판단에 필요한 시간 정보

현재 TASK_ATTEMPTS에는 `attempted_at`은 있지만 `started_at`, `completed_at`은 없다.

MVP에서는 attempted_at 기준으로 오래된 PENDING을 찾을 수 있지만, RUNNING 시간을 정확히 판단하려면 추가 timestamp 컬럼이 더 명확할 수 있다.

지금 문서 단계에서는 필요성만 기록하고 임의로 migration하지 않는다.

## 5. MVP 복구안

가장 단순한 후보:

```text
오래된 PENDING/RUNNING 조회
→ 정상 처리 시간이 명백히 지난 row 확인
→ SYSTEM_ERROR로 전환
→ 사용자는 다시 제출 가능
```

예를 들어 정확한 `stale_after_seconds` 값은 설정에서 관리하고 팀에서 확정한다.

중요: 특정 초 값을 문서에서 기획값으로 고정하지 않는다.

## 6. 언제 정리할까

후보 A: 서버 시작 시 1회

```text
FastAPI startup
→ 오래된 PENDING/RUNNING 정리
```

장점: 단순함.
단점: 서버가 계속 살아있는 동안 새 고착 row는 즉시 정리되지 않음.

후보 B: 결과 조회 시 lazy 정리

```text
GET /attempts/{id}
→ 너무 오래된 PENDING인지 확인
→ 필요 시 SYSTEM_ERROR 처리
```

장점: 별도 scheduler 없음.
단점: 아무도 조회하지 않는 row는 남음.

후보 C: 주기적 cleanup job

운영 규모가 커지면 검토.

MVP에서는 A+B 조합 정도가 이해하기 쉽다.

## 7. 자동 재실행 여부

고착 attempt를 서버가 자동으로 다시 Docker에 넣을 수도 있지만, 중복 실행과 중복 보상 위험이 커진다.

MVP 추천은:

```text
고착 → SYSTEM_ERROR
→ 사용자에게 재제출 안내
```

처럼 명시적으로 끝내는 쪽이 단순하다.

자동 retry는 작업 큐/멱등성이 더 잘 갖춰진 뒤 검토한다.

## 8. Docker cleanup

채점 함수는 성공/실패/timeout/예외 어느 경우든 컨테이너 제거를 시도해야 한다.

개념적으로:

```text
try
  container 실행
finally
  container stop/remove
```

형태의 정리가 필요하다.

서버 자체가 강제 종료된 경우 남은 컨테이너를 어떻게 찾을지도 운영 단계에서 검토할 수 있다.

## 9. SYSTEM_ERROR와 사용자 오류 구분

다음을 SYSTEM_ERROR로 분류할 수 있다.

- Docker Engine 연결 실패
- 이미지 없음
- 컨테이너 생성 실패
- 서버 내부 예외
- 작업 유실로 인한 stale 처리

반면 사용자 코드의 SyntaxError/NameError는 RUNTIME_ERROR 등 사용자 결과로 구분한다.

## 10. 보상 안전성

SYSTEM_ERROR 처리에서는:

```text
보상 없음
숙련도 변경 없음
```

이 기본이다.

이미 보상 transaction이 commit된 뒤 응답만 유실된 경우에는 단순 재처리하면 중복 보상이 생길 수 있으므로 보상 단계 자체가 멱등하게 설계되어야 한다.

## 11. 배틀/승급전 장애와 차이

실시간 배틀은 단순 BackgroundTask 복구와 다르다.

서버가 내려가면 WebSocket 연결도 끊기므로:

```text
재접속
현재 room 상태 재조회
점수 DB 기준 복원
```

정책이 필요하다.

승급전은 `expires_at`이 DB에 있으므로 서버가 잠시 내려갔다가 올라와도 서버 현재시각과 비교해 TIMEOUT을 판정할 수 있다.

## 12. 운영 로그

고착 정리 시 최소한 다음을 로그에 남기면 원인 분석이 쉽다.

```text
attempt_id
기존 status
attempted_at
정리 시각
SYSTEM_ERROR 전환 이유
```

submitted_code 전체를 일반 로그에 그대로 남길지는 개인정보/로그 크기를 고려한다.

## 13. 테스트

- PENDING 생성 후 grading 함수 미실행 상태
- RUNNING 중 Docker 예외
- TIMEOUT 후 컨테이너 cleanup
- stale threshold 이전에는 상태 유지
- threshold 이후 SYSTEM_ERROR
- SYSTEM_ERROR 후 새 attempt 재제출 가능
- stale 정리를 두 번 실행해도 추가 부작용 없음

## 향후 확장

서버가 여러 worker/인스턴스로 늘거나 채점 유실을 허용할 수 없게 되면:

```text
Redis/Celery 등 durable queue
작업 retry 횟수
dead-letter 개념
worker heartbeat
```

같은 구조를 검토할 수 있다.

현재 MVP에서 중요한 것은 복잡한 큐를 먼저 넣는 것이 아니라 **BackgroundTasks는 작업 유실 가능성이 있다는 사실을 알고 PENDING이 영원히 남지 않도록 최소 복구 규칙을 두는 것**이다.