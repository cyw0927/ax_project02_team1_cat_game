# C. 실시간 배틀 DB Before / After

이 문서는 방 생성부터 참가, Ready, Start, 점수, Finish까지 **배틀 상태가 DB에서 어떻게 바뀌는지** 정리한다.

현재 Lobby 기능은 상당 부분 구현돼 있지만 실제 채점·점수·WebSocket·보상은 아직 미구현이다.

점수 숫자와 시작/종료 규칙은 기획 확정 전 임의로 넣지 않는다.

---

## C-DB01. 방 생성 — 현재

### Before

```text
USERS.U1 존재
ROOMS에 새 방 없음
```

### 처리

```text
User 확인
→ title 검증
→ ROOMS INSERT
→ COMMIT
```

### After

```text
ROOMS.R1
host_user_id=U1
status=WAITING
max_participants=요청값
```

방장을 자동으로 `ROOM_PARTICIPANTS`에 넣을지는 아직 정책 미정이다.

---

## C-DB02. 정상 방 참가 — 현재

### Before

```text
ROOMS.R1 status=WAITING
participant_count < max_participants
U2는 아직 미참가
```

### 처리

```text
BEGIN
→ R1 SELECT ... FOR UPDATE
→ WAITING 확인
→ 중복 참가 확인
→ 참가자 수 확인
→ ROOM_PARTICIPANTS INSERT
→ COMMIT
```

### After

```text
ROOM_PARTICIPANTS.P2
room_id=R1
user_id=U2
current_score=0
is_ready=false
```

---

## C-DB03. 마지막 자리 경쟁 — 현재 핵심 동시성

### Before

```text
max_participants=4
현재 참가자=3
```

U4와 U5가 동시에 참가 요청.

### 처리

둘 다 같은 `ROOMS.R1` row를 lock하려고 한다.

한 요청이 먼저:

```text
lock
→ count=3
→ INSERT
→ COMMIT
```

다음 요청은 lock을 얻은 뒤 다시 count하여 4를 보고 거절된다.

### After

```text
최종 참가자 수 = 4 이하
```

---

## C-DB04. 중복 참가

### Before

```text
ROOM_PARTICIPANTS에 (R1,U2) 존재
```

### After

두 번째 참가 row 생성 없음.

DB의:

```text
UNIQUE(room_id, user_id)
```

도 최종 방어선이다.

---

## C-DB05. Ready 변경 — 현재

### Before

```text
R1 status=WAITING
P2 is_ready=false
```

### 처리

```text
participant 확인
→ is_ready=true
→ COMMIT
```

### After

```text
P2 is_ready=true
```

향후 WebSocket을 붙이면 **DB commit 후** `ready_changed`를 broadcast한다.

---

## C-DB06. ROOM_TASKS 추가 — 현재

### Before

```text
R1 WAITING
T1 active
```

### After

```text
ROOM_TASKS.RT1
room_id=R1
task_id=T1
task_order=1
```

핵심 제약:

```text
UNIQUE(room_id, task_id)
UNIQUE(room_id, task_order)
```

---

## C-DB07. 게임 시작 — 현재 PARTIAL

### Before

```text
R1 status=WAITING
```

현재 코드는 host와 WAITING만 확인한다.

### After

```text
R1 status=IN_PROGRESS
```

향후 최소 인원/Ready/문제 존재 조건이 확정되면 같은 Start transaction 안에서 재검사한다.

WebSocket은 commit 이후 `game_started`.

---

## C-DB08. 배틀 문제 정답 — 향후

### 필요한 Before

```text
R1 status=IN_PROGRESS
P2는 R1 참가자
T1은 R1 ROOM_TASKS
```

그리고 가장 중요한 사실:

```text
P2가 T1에서 이미 점수를 받았는가?
```

를 확인할 영속 기록이 필요하다.

### 처리 목표

```text
서버 채점 완료
→ BEGIN
→ room/participant/문제/중복 득점 상태 재확인
→ 점수 기록을 최초 성공으로 확정
→ ROOM_PARTICIPANTS.current_score 증가
→ COMMIT
→ score_changed broadcast
```

### After

```text
P2.current_score = 서버 계산 최종값
문제별 득점 이력 = 1회성 확인 가능 상태
```

현재 ERD에서는 두 번째 줄의 저장 구조가 부족하다.

---

## C-DB09. 같은 문제 동시 정답 제출 — P0

### 위험한 Before

동일한 U2/R1/T1 제출 A와 B가 동시에 정답.

### 잘못된 결과

```text
A가 점수 증가
B도 점수 증가
```

### 올바른 After 목표

```text
문제별 허용 점수 횟수만 반영
current_score 중복 증가 없음
```

이 테스트를 통과할 수 있는 DB 구조를 scoring 구현 전에 확정해야 한다.

---

## C-DB10. 오답

정책에 따라 감점이 없다고 확정되지 않았다.

따라서 현재 문서의 목표는:

```text
서버가 WRONG 결과를 판정
→ 기획에서 정한 점수 변화만 반영
```

이다.

정책이 무감점이면 DB score 변화 없음, 감점이면 서버 규칙만큼 변경한다.

---

## C-DB11. WebSocket 이벤트 실패

### Before

점수 transaction이 정상 commit.

### 그 뒤

WebSocket broadcast가 실패.

### After

```text
DB 점수는 commit된 최종값 유지
```

WebSocket 전송 실패 때문에 이미 확정된 DB 게임 상태를 rollback하지 않는다.

클라이언트는 재접속 snapshot으로 복구한다.

---

## C-DB12. 재접속

### Before

socket connection registry는 사라졌거나 연결 끊김.

DB:

```text
ROOMS status
ROOM_PARTICIPANTS Ready/score
ROOM_TASKS order
```

는 남아 있음.

### After

DB 변화 없이 현재 snapshot을 읽어 화면을 복구한다.

경기 `current_task_order` 같은 진행 위치가 필요하면 현재 스키마 갭을 별도 해결한다.

---

## C-DB13. 게임 종료 — 현재

### Before

```text
R1 status=IN_PROGRESS
```

### 현재 처리

host 요청으로:

```text
R1 status=FINISHED
→ COMMIT
```

### After

```text
R1 status=FINISHED
```

현재는 순위/결과/보상 저장이 없다.

---

## C-DB14. 결과 보상 — 향후

### 목표 transaction

최종 결과를 최초로 확정하는 시점에:

```text
BEGIN
→ room이 아직 보상 처리 가능한 상태인지 확인
→ 순위/승자 판정
→ 대상 사용자 재화 증가
→ 보상 1회성 상태 확정
→ COMMIT
```

### After 목표

같은 finish/result 로직을 다시 호출해도:

```text
추가 보상 없음
```

현재 ERD에는 `reward_processed` 같은 명시 상태가 없어 구조 결정이 필요하다.

---

# 한눈에 보는 핵심

```text
방 참가
ROOMS row lock → 인원/상태 확인 → participant INSERT

배틀 점수
서버 채점 → 문제별 중복 득점 방어 → current_score commit → WS broadcast

재접속
WebSocket 메모리가 아니라 DB snapshot 복구

결과 보상
최초 완료 처리에서만 1회 지급
```

배틀 DB의 가장 큰 미해결점은 **사용자-방-문제 단위의 득점 이력**이다. 이 부분을 해결하기 전에는 scoring을 완료 처리하지 않는다.
