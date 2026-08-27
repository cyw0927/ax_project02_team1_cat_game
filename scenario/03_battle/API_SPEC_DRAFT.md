# C. 실시간 배틀 API 명세 초안

이 문서는 `03_battle` 시나리오를 실제 REST/WebSocket 계약으로 옮기기 위한 초안이다.

현재 `main`에는 방 생성/입장/Ready/Start/Finish/ROOM_TASKS까지 구현돼 있고, 실제 문제 제출·채점·점수·WebSocket·보상은 아직 없다.

점수 숫자, 시작 최소 인원, Ready 규칙, 종료 조건 등 미정 비즈니스 규칙은 이 문서에서 임의로 확정하지 않는다.

---

## 1. 방 목록

### Endpoint

```http
GET /rooms
```

### 현재 구현

구현됨.

### Response

```json
[
  {
    "id": "room-uuid",
    "title": "방 제목",
    "host_user_id": "user-uuid",
    "status": "WAITING",
    "max_participants": 4
  }
]
```

### 향후 확장 후보

- WAITING만 filter
- page/size
- 현재 인원수

---

## 2. 방 생성

### Endpoint

```http
POST /rooms
```

### 현재 Request

```json
{
  "title": "방 제목",
  "host_user_id": "user-uuid",
  "max_participants": 4
}
```

### JWT 적용 후 후보

```json
{
  "title": "방 제목",
  "max_participants": 4
}
```

방장은 JWT 사용자로 결정한다.

### 현재 처리

```text
host User 확인
→ title trim/빈 문자열 검사
→ ROOMS(status=WAITING) INSERT
→ COMMIT
```

### 미정

방 생성 즉시 방장을 `ROOM_PARTICIPANTS`에 자동 참가시킬지.

---

## 3. 방 참가

### 현재 Endpoint

```http
POST /rooms/{room_id}/participants
```

### Request

```json
{
  "user_id": "user-uuid",
  "team_name": null
}
```

JWT 적용 후 user_id 제거 후보.

### 현재 백엔드 처리

```text
User 확인
→ ROOMS SELECT ... FOR UPDATE
→ room 존재
→ WAITING 확인
→ 중복 참가 확인
→ 현재 참가자 count
→ max_participants 확인
→ ROOM_PARTICIPANTS INSERT
→ COMMIT
```

### 핵심 동시성

마지막 한 자리를 여러 사용자가 동시에 요청해도 room row lock 때문에 정원을 넘기지 않도록 한다.

### 상태코드

- 성공: `201 Created`
- 사용자/방 없음: `404`
- 이미 참가/방 full/WAITING 아님: `409`

---

## 4. 참가자 목록

### Endpoint

```http
GET /rooms/{room_id}/participants
```

### 현재 구현

구현됨.

### Response 필드

```text
user_id
username
team_name
current_score
is_ready
```

---

## 5. 내 참여 방 목록

### Endpoint

```http
GET /users/{user_id}/rooms
```

### 현재 구현

구현됨.

JWT 이후 `/me/rooms` 후보.

---

## 6. Ready 변경

### 현재 Endpoint

```http
PATCH /rooms/{room_id}/participants/{user_id}/ready
```

### Request

```json
{
  "is_ready": true
}
```

### 현재 처리

```text
room 존재
→ WAITING 확인
→ room participant 확인
→ is_ready UPDATE
→ COMMIT
```

### 보안 갭

현재 path의 `user_id`를 인증 사용자와 대조하지 않으므로 JWT 적용 후 ownership 검사가 필요하다.

### 실시간 연결

최종적으로 commit 후:

```text
ready_changed
```

WebSocket 이벤트 broadcast 후보.

---

## 7. ROOM_TASKS 추가

### Endpoint

```http
POST /rooms/{room_id}/tasks
```

### 현재 Request

```json
{
  "user_id": "host-uuid",
  "task_id": "task-uuid",
  "task_order": 1
}
```

### 현재 검사

```text
room 존재
→ 요청자가 host
→ WAITING
→ active task 존재
→ 동일 task 중복 없음
→ 동일 task_order 중복 없음
→ INSERT
```

### 핵심 제약

```text
UNIQUE(room_id, task_id)
UNIQUE(room_id, task_order)
```

---

## 8. ROOM_TASKS 삭제

### Endpoint

```http
DELETE /rooms/{room_id}/tasks/{task_id}
```

현재 body에서 `user_id`를 받는다.

JWT 이후 host 권한은 토큰 사용자로 판단하는 쪽이 안전하다.

---

## 9. ROOM_TASKS 조회

### Endpoint

```http
GET /rooms/{room_id}/tasks
```

### 현재 구현

구현됨.

Response에는:

```text
task_order
task_id
concept_id
type
difficulty
template_code
```

를 보내고 `test_cases`는 숨긴다.

---

## 10. 게임 시작

### Endpoint

```http
POST /rooms/{room_id}/start
```

### 현재 Request

```json
{
  "user_id": "host-uuid"
}
```

### 현재 검사

```text
room 존재
→ 요청자가 host
→ status == WAITING
→ IN_PROGRESS로 변경
```

### 현재 상태

**PARTIAL**.

아직 다음은 검사하지 않는다.

```text
최소 참가자 수
Ready 조건
ROOM_TASKS 존재/개수
팀 구성 조건
```

기획 확정 후 Start transaction 안에서 검사한다.

commit 후 `game_started` WebSocket 이벤트를 보낸다.

---

## 11. 배틀 문제 제출

### Endpoint 후보

```http
POST /rooms/{room_id}/tasks/{task_id}/attempts
```

### 현재 상태

미구현.

### Request 후보

```json
{
  "submitted_code": "..."
}
```

사용자/점수/정답 여부는 프론트가 보내지 않는다.

### 서버 처리 후보

```text
JWT user 확인
→ room participant인지
→ room IN_PROGRESS인지
→ room task인지
→ 이미 득점한 문제인지
→ 채점 접수/실행
→ PASSED면 점수 반영
→ COMMIT
→ score_changed broadcast
```

---

## 12. 중복 득점 문제

현재 ERD의 핵심 갭이다.

현재 저장 가능:

```text
participant.current_score
room tasks
```

하지만 다음 사실은 저장하지 못한다.

```text
이 사용자가 이 방의 이 문제에서 이미 점수를 받았는가?
```

따라서 scoring API 구현 전에 저장 구조를 확정해야 한다.

이 구조가 해결되지 않은 상태에서 메모리 bool만으로 완료 처리하지 않는다.

---

## 13. 점수 Response / WebSocket

REST 제출 결과와 별개로 다른 참가자에게는 commit 후:

```json
{
  "type": "score_changed",
  "room_id": "room-uuid",
  "payload": {
    "participant_id": "participant-uuid",
    "current_score": "서버 최종 점수"
  }
}
```

형태를 사용할 수 있다.

`delta`만 보내기보다 최종 `current_score`를 보내는 편이 중복 이벤트에 안전하다.

---

## 14. 게임 종료

### 현재 Endpoint

```http
POST /rooms/{room_id}/finish
```

### 현재 처리

```text
room 존재
→ 요청자가 host
→ IN_PROGRESS 확인
→ FINISHED
→ COMMIT
```

### 현재 상태

**PARTIAL**.

아직:

```text
종료 조건
최종 순위
동점
팀 점수
결과 보상
보상 1회성
```

이 없다.

실제 게임에서는 수동 Finish가 운영용인지, 자동 종료가 기준인지도 확정해야 한다.

---

## 15. 결과 조회

### Endpoint 후보

```http
GET /rooms/{room_id}/result
```

### 현재 상태

미구현.

Response 후보:

```json
{
  "room_id": "room-uuid",
  "status": "FINISHED",
  "results": []
}
```

순위/팀/보상 필드는 기획 확정 후 정한다.

---

## 16. WebSocket

### Endpoint 후보

```text
/ws/rooms/{room_id}
```

정확한 URL은 프론트와 합의한다.

### 서버가 확인

```text
JWT 유효
→ room 존재
→ ROOM_PARTICIPANTS에 사용자 존재
→ 연결 허용
```

### 이벤트 후보

```text
participant_joined
participant_left
ready_changed
game_started
score_changed
game_finished
```

DB commit 후 broadcast가 원칙이다.

---

## 17. 재접속

WebSocket 이벤트 자체를 영속 상태로 믿지 않는다.

재접속 시:

```text
JWT 확인
→ room/participant DB 조회
→ status/participants/score/tasks snapshot
→ socket 재연결
```

현재 `current_task_order` 같은 경기 진행 위치는 ERD에 없어 추가 설계 가능성이 있다.

---

# C 영역 현재 완료 판정

```text
방 목록/생성              DONE
방 참가                    DONE
Ready                      DONE(인증 ownership 미적용)
ROOM_TASKS CRUD            DONE
Start                      PARTIAL
Finish                     PARTIAL
배틀 문제 제출             MISSING
실제 채점                  MISSING
중복 득점 방어             POLICY/P0
점수 증가                  MISSING
WebSocket                  MISSING
재접속 snapshot            MISSING
순위/결과                  MISSING
결과 보상                  MISSING/POLICY
JWT                        MISSING
```

# 구현 전 핵심 결정

1. 방장 자동 참가 여부
2. 최소 시작 인원
3. Ready 조건
4. 개인전/팀전 범위
5. 정답/오답/속도 점수 규칙
6. 재도전 정책
7. 사용자-방-문제 중복 득점 저장 구조
8. 종료 조건/동점
9. 결과 보상/1회 지급 기록
10. 경기 진행 위치를 DB에 저장할지

이 항목을 확정한 뒤 scoring과 realtime을 구현한다.
