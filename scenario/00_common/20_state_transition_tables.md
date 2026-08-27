# 상태 전이표(State Transition Tables)

이 문서는 `status` 같은 상태값이 **어떤 순서로 바뀌어야 하는지**를 정리한 초안이다.

상태값은 단순 문자열이 아니라 서버가 허용해야 하는 행동을 결정하는 기준이다. 예를 들어 `FINISHED`인 배틀방을 다시 시작하게 해서는 안 되고, `TIMEOUT`된 승급전에 코드를 저장하게 해서도 안 된다.

---

# 1. TASK_ATTEMPTS 상태 전이

추천 상태값 초안:

```text
PENDING
RUNNING
PASSED
WRONG_ANSWER
RUNTIME_ERROR
TIMEOUT
SYSTEM_ERROR
```

정확한 상태값 명칭은 팀 확정 전까지 초안으로 본다.

## 정상 전이

```text
PENDING
  ↓
RUNNING
  ├─→ PASSED
  ├─→ WRONG_ANSWER
  ├─→ RUNTIME_ERROR
  ├─→ TIMEOUT
  └─→ SYSTEM_ERROR
```

BackgroundTasks가 실행 슬롯을 기다리는 동안은 `PENDING`, 실제 Docker 실행 직전에 `RUNNING`으로 바꾸는 구조가 이해하기 쉽다.

## 허용하면 안 되는 전이 예

```text
PASSED → RUNNING ❌
WRONG_ANSWER → PASSED ❌
TIMEOUT → RUNNING ❌
SYSTEM_ERROR → PASSED ❌
```

재제출은 기존 attempt 상태를 되돌리는 것이 아니라 **새 TASK_ATTEMPTS row를 만드는 것**이다.

## 왜 중요한가

```text
1차 attempt = WRONG_ANSWER
2차 attempt = PASSED
```

이어야 학습 이력이 남는다.

기존 row를:

```text
WRONG_ANSWER → PASSED
```

로 덮어쓰면 첫 번째 오답 기록이 사라진다.

---

# 2. ROOMS 상태 전이

현재 ERD 상태:

```text
WAITING
IN_PROGRESS
FINISHED
```

## 정상 전이

```text
WAITING
   ↓
IN_PROGRESS
   ↓
FINISHED
```

## WAITING에서 가능한 행동

- 참가자 입장
- Ready 변경
- 방장이 ROOM_TASKS 구성
- 조건 충족 후 시작
- 필요하면 참가자 퇴장

## IN_PROGRESS에서 가능한 행동

- 배틀 문제 진행
- 점수 반영
- WebSocket 이벤트
- 재접속 처리
- 종료 조건 판정

## FINISHED에서 가능한 행동

- 최종 결과 조회
- 승자/점수 표시

기본적으로 신규 입장, Ready 변경, 문제 목록 변경, 재시작은 금지한다.

## 금지 전이

```text
FINISHED → WAITING ❌
FINISHED → IN_PROGRESS ❌
IN_PROGRESS → WAITING ❌
```

재경기를 만들고 싶다면 기존 방 상태를 되돌리는 것보다 새로운 ROOM을 생성하는 방식이 단순하다.

---

# 3. ROOM_PARTICIPANTS Ready 상태

Ready는 room 상태와 함께 해석해야 한다.

```text
WAITING에서만
false ↔ true
```

게임 시작 후에는 `is_ready`를 바꿀 필요가 없다.

방장 Ready 정책은 아직 미정이다.

후보:

```text
A. 방장도 Ready 필요
B. 방장은 Ready 없이 Start 가능
C. 방장은 자동 Ready
```

이 규칙을 코드 전에 확정한다.

---

# 4. RANK_CHALLENGES 상태 전이

현재 ERD:

```text
IN_PROGRESS
SUCCESS
FAILED
TIMEOUT
```

## 정상 전이

```text
IN_PROGRESS
   ├─→ SUCCESS
   ├─→ FAILED
   └─→ TIMEOUT
```

`SUCCESS`, `FAILED`, `TIMEOUT`은 모두 종료 상태다.

## 종료 후 금지

```text
SUCCESS → IN_PROGRESS ❌
FAILED → IN_PROGRESS ❌
TIMEOUT → IN_PROGRESS ❌
```

다시 도전하려면 새로운 `RANK_CHALLENGES` row를 만든다.

## TIMEOUT 판정

클라이언트가 보내는 타이머 값을 믿지 않는다.

```text
server_now >= expires_at
```

이면 TIMEOUT 처리한다.

코드 저장/제출 API가 들어올 때마다 현재 시간과 expires_at을 확인해야 한다.

---

# 5. RANK_CHALLENGE_TASKS 상태

이 테이블은 별도 status 문자열 대신:

```text
is_passed
saved_code
```

로 문제별 진행 상황을 관리한다.

간단한 흐름:

```text
문제 생성
is_passed = false
saved_code = null 또는 template
     ↓
코드 작성
saved_code 갱신
     ↓
채점 통과
is_passed = true
```

이미 `is_passed=true`인 문제를 다시 제출할 수 있는지는 기획 정책이 필요하다.

MVP에서는 다시 제출하더라도 challenge 성공 조건에 추가 효과가 없도록 하는 편이 단순하다.

---

# 6. 사용자 보상 상태는 별도 status가 없음

현재 ERD에서는 `USERS.balance`, `USERS.mileage`를 숫자로 직접 가지고 있다.

그래서 보상 지급은 상태 전이가 아니라 transaction으로 이해해야 한다.

예:

```text
TASK_ATTEMPT PASSED 확정
+ 최초 정답 조건 충족
        ↓
USERS.balance 증가
```

여기서 가장 중요한 것은:

```text
PASSED 저장은 됐는데 보상 실패
또는
보상은 됐는데 PASSED 저장 실패
```

같은 반쪽 transaction을 막는 것이다.

보상 지급을 같은 DB transaction에서 처리할지, 별도 보상 처리 단계로 분리할지는 기능별로 결정한다.

---

# 7. 상태 검사 패턴

백엔드 endpoint는 값을 바꾸기 전에 현재 상태를 먼저 확인한다.

예: 방 시작

```text
현재 room.status 확인
↓
WAITING인가?
↓
YES → 다른 시작 조건 검사
NO → 409
```

예: 승급전 코드 저장

```text
challenge.status 확인
↓
IN_PROGRESS인가?
↓
expires_at 안 지났는가?
↓
YES → saved_code UPDATE
NO → 거부/TIMEOUT
```

---

# 8. 상태 전이를 DB에서 어디까지 강제할까

선택지는 두 가지다.

### 애플리케이션에서 검사

Python/FastAPI에서:

```text
if room.status != "WAITING":
    reject
```

구현하기 쉽고 초보자가 이해하기 좋다.

### DB CHECK/ENUM 활용

허용 가능한 문자열 자체를 DB에서 제한할 수 있다.

예:

```text
ROOMS.status는 WAITING/IN_PROGRESS/FINISHED만 허용
```

그러나 `WAITING → FINISHED` 같은 **전이 순서 자체**는 CHECK만으로 막기 어렵다.

따라서 MVP 추천은:

```text
허용 상태값 범위 → DB/모델 제약 검토
상태 전이 순서 → 백엔드 로직 + 테스트
```

이다.

---

# 9. 테스트해야 할 전이

## TASK_ATTEMPTS

```text
PENDING → RUNNING → PASSED
PENDING → RUNNING → WRONG_ANSWER
PENDING → RUNNING → RUNTIME_ERROR
PENDING → RUNNING → TIMEOUT
PENDING → RUNNING → SYSTEM_ERROR
```

## ROOMS

```text
WAITING → IN_PROGRESS
IN_PROGRESS → FINISHED
FINISHED 상태에서 start 요청 거부
```

## RANK_CHALLENGES

```text
IN_PROGRESS → SUCCESS
IN_PROGRESS → FAILED
IN_PROGRESS → TIMEOUT
TIMEOUT 후 code 저장 거부
SUCCESS 후 재제출 거부/무효화
```

상태 기반 기능은 Happy Path만 테스트하면 안 된다. **이미 종료된 상태에서 같은 API를 다시 호출하는 테스트**가 특히 중요하다.