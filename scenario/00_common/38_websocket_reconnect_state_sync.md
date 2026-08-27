# WebSocket 재접속·상태 동기화 정책

이 문서는 실시간 배틀에서 WebSocket 연결이 끊겼다가 다시 연결될 때 **무엇을 믿고 어떻게 현재 상태를 복구할지** 정리한다.

핵심 원칙은 하나다.

```text
WebSocket = 실시간 전달 수단
DB = 최종 상태의 기준
```

WebSocket 이벤트를 놓쳤다고 해서 게임 상태 자체가 사라지면 안 된다.

---

## 1. 왜 재접속이 필요한가

모바일 환경에서는 다음이 흔하다.

- Wi-Fi ↔ LTE 전환
- 화면 잠금
- 앱 백그라운드 이동
- 순간 네트워크 단절
- 서버 재시작

따라서 `연결이 끊기면 게임 종료`로만 만들면 사용성이 좋지 않다.

---

## 2. 정상 접속 흐름

```text
REST로 room 입장/현재 상태 조회
→ WebSocket 연결
→ 서버가 room 참가자 확인
→ 이후 실시간 이벤트 수신
```

WebSocket 연결 자체만으로 방 참가 row를 새로 만들지 않는다.

방 참가의 영속 상태는 `ROOM_PARTICIPANTS`가 기준이다.

---

## 3. 재접속 흐름

추천 흐름:

```text
연결 끊김
→ 프론트 재접속 시도
→ JWT로 사용자 식별
→ room_id로 현재 DB 상태 조회
→ 참가자인지 확인
→ room status 확인
→ 현재 참가자/점수/Ready/진행상태 snapshot 반환
→ WebSocket 다시 구독
```

중요:

```text
놓친 이벤트를 전부 재생
```

하는 복잡한 구조보다 MVP에서는 **현재 상태 snapshot을 다시 받는 방식**이 단순하다.

---

## 4. 무엇을 복구해야 하나

최소:

- ROOMS.status
- ROOM_PARTICIPANTS 목록
- 각 participant의 is_ready
- 각 participant의 current_score
- ROOM_TASKS 순서

배틀 중 현재 몇 번째 문제인지 별도 상태가 필요하다면 현재 ERD만으로 충분한지 검토해야 한다.

현재 ERD에는 `current_task_order` 같은 room 진행 위치 컬럼이 없다.

---

## 5. 이벤트와 DB 순서

실시간 상태 변경은 가능하면:

```text
DB COMMIT
→ WebSocket broadcast
```

순서로 한다.

예:

```text
Ready 변경 DB commit
→ ready_changed 이벤트
```

DB commit 전에 이벤트를 보내면 rollback 시 화면과 DB가 어긋날 수 있다.

---

## 6. 이벤트 예시

최종 이벤트명은 프론트와 합의하되 개념적으로 다음 정도가 있다.

```text
participant_joined
participant_left
ready_changed
game_started
score_changed
game_finished
```

이벤트 payload에는 전체 room snapshot을 매번 보낼 수도 있고, 변경분만 보낼 수도 있다.

MVP에서는 변경분 + 필요 시 REST snapshot 재조회가 단순하다.

---

## 7. 연결 인증

WebSocket도 HTTP API와 같은 사용자 식별 원칙을 따른다.

- user_id를 query/body로 받아 그대로 믿지 않는다.
- JWT 등 인증 수단으로 사용자 식별.
- 해당 사용자가 실제 room participant인지 확인.

인증 방식 자체는 `41_auth_jwt_detailed_flow.md`에서 별도 정리한다.

---

## 8. 방이 이미 끝난 경우

재접속했는데:

```text
ROOMS.status = FINISHED
```

이면 게임 화면을 재개하지 않고 최종 결과 화면으로 전환할 수 있다.

프론트는 WebSocket 연결 성공 여부가 아니라 **서버 room 상태**를 기준으로 화면을 결정한다.

---

## 9. 서버 재시작

서버가 재시작되면 기존 WebSocket connection registry는 사라질 수 있다.

하지만 DB에:

- room
- participant
- score
- status

가 남아 있다면 사용자는 다시 연결하여 snapshot을 받을 수 있다.

따라서 connection manager의 메모리 상태를 게임 결과의 유일한 기준으로 사용하지 않는다.

---

## 10. heartbeat

운영 단계에서는 ping/pong 또는 heartbeat를 둘 수 있다.

목적:

- 끊긴 connection 정리
- 오래된 socket 감지

하지만 heartbeat 주기 숫자는 지금 임의로 확정하지 않는다.

---

## 11. 중복 연결

한 사용자가 같은 room에 여러 socket을 열 수 있다.

정책 후보:

A. 여러 연결 허용
B. 마지막 연결만 유지
C. 같은 user-room 1개만 유지

MVP에서는 구현 단순성을 우선해 선택하되 팀 합의가 필요하다.

---

## 12. 테스트

- 정상 연결
- 참가자가 아닌 사용자 연결 거절
- Ready 후 연결 끊기고 재접속
- 점수 증가 후 재접속
- FINISHED 이후 재접속
- 서버 재시작 후 snapshot 복구
- 같은 사용자의 중복 연결
- commit 실패 시 이벤트가 먼저 나가지 않는지

---

# 결론

MVP에서 가장 중요한 것은 이벤트 유실을 완벽히 없애는 것이 아니다.

```text
WebSocket이 끊겨도
→ DB에 현재 상태가 남고
→ 다시 연결하면 snapshot으로 복구 가능
```

하게 만드는 것이 우선이다.