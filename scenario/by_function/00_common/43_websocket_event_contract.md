# WebSocket 이벤트 계약 초안

이 문서는 실시간 배틀에서 프론트와 백엔드가 주고받는 WebSocket 메시지를 **어떤 공통 모양으로 맞출지** 정리한다.

`38_websocket_reconnect_state_sync.md`가 "끊겼을 때 어떻게 복구할지"를 설명한다면, 이 문서는 **연결된 동안 어떤 이벤트를 어떤 형태로 주고받을지**에 집중한다.

> 이벤트 이름과 필드명은 초안이다. 프론트와 합의한 뒤 확정한다.

---

## 1. 핵심 원칙

```text
REST = 상태를 만들거나 현재 snapshot을 조회
WebSocket = 이미 확정된 상태 변경을 실시간 전달
DB = 최종 진실의 기준
```

예를 들어 Ready 변경은:

```text
PATCH Ready
→ DB COMMIT
→ ready_changed WebSocket broadcast
```

순서가 기본이다.

WebSocket 이벤트를 먼저 보낸 뒤 DB가 rollback되는 구조는 피한다.

---

## 2. 서버 → 클라이언트 공통 Envelope 후보

```json
{
  "type": "ready_changed",
  "room_id": "room-uuid",
  "server_time": "2026-08-27T10:00:00Z",
  "payload": {}
}
```

공통 필드 후보:

- `type`: 어떤 이벤트인지
- `room_id`: 어느 방의 이벤트인지
- `server_time`: 서버가 이벤트를 만든 시각
- `payload`: 이벤트별 실제 데이터

필요해지면 `event_id`를 추가할 수 있다.

`event_id`는 중복 이벤트 감지나 디버깅에는 도움이 되지만 MVP에서 무조건 필요한 것은 아니다.

---

## 3. participant_joined

사용자가 방 입장 transaction을 성공한 뒤 전송.

```json
{
  "type": "participant_joined",
  "room_id": "room-uuid",
  "payload": {
    "participant_id": "participant-uuid",
    "user_id": "user-uuid",
    "team_name": null,
    "is_ready": false,
    "current_score": 0
  }
}
```

프론트는 참가자 목록에 새 사용자를 표시한다.

중요:

```text
이 이벤트 수신
≠ DB에 새 참가자를 만드는 요청
```

DB INSERT는 REST join API에서 이미 끝난 상태다.

---

## 4. participant_left

퇴장 기능이 확정될 경우 사용.

```json
{
  "type": "participant_left",
  "room_id": "room-uuid",
  "payload": {
    "participant_id": "participant-uuid"
  }
}
```

WAITING과 IN_PROGRESS에서 퇴장을 어떻게 처리할지는 별도 비즈니스 규칙이 필요하다.

---

## 5. ready_changed

```json
{
  "type": "ready_changed",
  "room_id": "room-uuid",
  "payload": {
    "participant_id": "participant-uuid",
    "is_ready": true
  }
}
```

프론트는 해당 참가자의 Ready 표시만 바꿀 수 있다.

---

## 6. game_started

방장이 시작 조건을 만족해 `ROOMS.status = IN_PROGRESS`가 commit된 뒤 전송.

```json
{
  "type": "game_started",
  "room_id": "room-uuid",
  "payload": {
    "status": "IN_PROGRESS"
  }
}
```

현재 문제 순서/시작시각을 payload에 넣을지는 배틀 진행상태 스키마 확정 뒤 결정한다.

---

## 7. score_changed

서버 채점 결과가 실제 점수에 반영된 뒤 전송.

```json
{
  "type": "score_changed",
  "room_id": "room-uuid",
  "payload": {
    "participant_id": "participant-uuid",
    "current_score": 300
  }
}
```

가능하면 `+100` 같은 delta만 보내기보다 **변경 후 최종 점수**를 같이 보내는 편이 화면 복구에 유리하다.

점수 숫자 자체는 기획 확정 전 임의로 고정하지 않는다.

---

## 8. game_finished

```json
{
  "type": "game_finished",
  "room_id": "room-uuid",
  "payload": {
    "status": "FINISHED",
    "results": []
  }
}
```

`results` 안에 순위/팀 결과/보상을 어느 정도까지 담을지는 배틀 결과 API 계약과 함께 결정한다.

WebSocket은 결과 화면 이동 신호를 주고, 필요하면 프론트가 REST로 최종 결과를 다시 조회하는 방식도 가능하다.

---

## 9. snapshot / resync

이벤트를 놓쳤거나 재접속한 경우 모든 과거 이벤트를 재생하는 대신 현재 snapshot을 다시 받는 방식을 우선한다.

후보:

```text
GET /rooms/{room_id}
GET /rooms/{room_id}/participants
GET /rooms/{room_id}/tasks
```

또는 WebSocket 연결 직후 서버가 snapshot 이벤트를 한 번 보내는 방법도 있다.

예:

```json
{
  "type": "room_snapshot",
  "room_id": "room-uuid",
  "payload": {
    "status": "IN_PROGRESS",
    "participants": [],
    "tasks": []
  }
}
```

어느 방식을 쓸지는 프론트 구현 난이도와 함께 확정한다.

---

## 10. 클라이언트 → 서버 메시지

모든 상태 변경을 WebSocket 명령으로 만들 필요는 없다.

MVP에서는 다음처럼 분리하는 편이 이해하기 쉽다.

```text
방 입장/Ready/Start/코드 제출
→ REST

다른 사용자에게 상태 변화 전달
→ WebSocket
```

나중에 정말 실시간 입력이 필요하면 client message type을 추가한다.

---

## 11. 오류 메시지

WebSocket 연결 자체에서 오류를 보낼 필요가 있다면 공통 형태 후보:

```json
{
  "type": "error",
  "payload": {
    "code": "NOT_ROOM_PARTICIPANT",
    "message": "방 참가자가 아닙니다."
  }
}
```

다만 REST 요청 실패는 해당 REST Response로 처리한다. 같은 오류를 REST와 WebSocket 양쪽에서 중복 전송할 필요는 없다.

---

## 12. 인증

연결 시 서버가 확인할 것:

```text
JWT 유효
→ 사용자 식별
→ room 존재
→ 해당 사용자가 ROOM_PARTICIPANTS에 존재
→ 연결 허용
```

프론트가 보내는 `user_id` 문자열만 보고 다른 사용자 socket으로 인정하면 안 된다.

---

## 13. 중복 이벤트

네트워크 환경이나 재연결 구조 때문에 프론트가 비슷한 이벤트를 여러 번 받을 수 있다.

따라서 가능하면 UI는:

```text
score += delta
```

보다:

```text
score = current_score
```

처럼 서버의 최종값으로 덮어쓰는 것이 안전하다.

---

## 14. 이벤트 순서

동일한 room에서 이벤트 순서가 중요할 수 있다.

예:

```text
score_changed
→ game_finished
```

MVP single-process에서는 전송 순서를 최대한 보존하되, 클라이언트는 최종적으로 DB snapshot을 다시 조회해 복구할 수 있어야 한다.

멀티 인스턴스가 되면 메시지 브로커 등 추가 설계가 필요할 수 있으나 현재 범위에서는 과도하게 확장하지 않는다.

---

## 15. 테스트

- 참가자 입장 후 다른 사용자에게 joined 이벤트 도착
- Ready commit 후 ready_changed
- DB rollback 시 이벤트 미전송
- 점수 증가 후 최종 current_score 일치
- 게임 종료 후 game_finished
- 연결 끊김 후 snapshot으로 상태 복구
- 참가자가 아닌 사용자의 socket 연결 거절
- 동일 이벤트를 두 번 받아도 UI 점수가 중복 증가하지 않음

---

# 결론

WebSocket 이벤트는 게임 상태 자체가 아니라 **게임 상태가 바뀌었다는 실시간 알림**으로 본다.

```text
DB 상태 변경 성공
→ commit
→ WebSocket 이벤트
→ 프론트 갱신

이벤트 유실/재접속
→ REST 또는 snapshot으로 현재 DB 상태 복구
```

이 원칙을 지키면 실시간 기능이 추가돼도 데이터 기준점이 흔들리지 않는다.