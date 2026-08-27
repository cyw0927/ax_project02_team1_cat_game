# C. 실시간 배틀 테스트 케이스

표기:

- **NOW**: 현재 코드로 테스트 가능
- **AFTER**: 구현 후 테스트
- **POLICY**: 시작/점수/종료/보상 규칙 확정 후 기대값 고정

---

## C-T01. 방 생성 — NOW

`POST /rooms`

**Then**
- `201`
- title trim 적용
- `status=WAITING`
- host user 존재 확인
- 빈 제목 거절

---

## C-T02. 방 목록 — NOW

`GET /rooms`

**Then** 방 기본 정보가 조회되고 DB 변경 없음.

---

## C-T03. 정상 방 참가 — NOW

**Then**
- `201`
- ROOM_PARTICIPANTS 생성
- current_score=0
- is_ready=false

---

## C-T04. 중복 참가 — NOW

같은 user가 같은 room에 다시 참가하면 `409`, 참가자 row는 1개여야 한다.

---

## C-T05. 마지막 자리 동시 참가 — NOW

정원이 1자리 남은 room에 여러 사용자가 동시에 요청한다.

**Then**
- max_participants 초과 없음
- `ROOMS FOR UPDATE`로 경쟁 구간 직렬화

---

## C-T06. 진행 중/종료 room 참가 거절 — NOW

WAITING이 아니면 참가 실패, participant 추가 없음.

---

## C-T07. Ready 정상 변경 — NOW

WAITING 참가자가 Ready를 true/false로 변경할 수 있다.

---

## C-T08. Ready 권한 위조 — AFTER JWT

사용자 A가 사용자 B의 Ready를 path user_id만 바꿔 수정할 수 없어야 한다.

---

## C-T09. ROOM_TASKS 추가 — NOW

host + WAITING + active task 조건에서 성공.

- 같은 task 중복 거절
- 같은 task_order 중복 거절
- 비활성 task 거절

---

## C-T10. ROOM_TASKS 삭제 — NOW

host만 WAITING에서 삭제 가능하고 다른 사용자는 거절된다.

---

## C-T11. Start 권한 — NOW

host만 WAITING room을 시작할 수 있다.

non-host는 `403`, 이미 시작된 room은 `409`.

---

## C-T12. Start 조건 — AFTER/POLICY

기획 확정 후 최소 인원, Ready, ROOM_TASKS 등의 조건을 하나씩 깨뜨려 Start가 거절되는지 확인한다.

현재 코드는 host/WAITING만 검사하므로 PARTIAL이다.

---

## C-T13. 배틀 제출 권한 — AFTER

참가자가 아닌 user, 다른 room의 task, FINISHED room 제출은 거절한다.

---

## C-T14. 정답 점수 반영 — AFTER/POLICY

서버 채점이 PASSED일 때만 current_score가 확정 점수 규칙대로 증가해야 한다.

프론트가 score를 직접 보내지 않는다.

---

## C-T15. 오답 점수 처리 — AFTER/POLICY

오답 감점/재도전 정책 확정 후 기대 점수와 상태를 검증한다.

---

## C-T16. 동일 문제 중복 득점 — AFTER/P0

같은 user-room-task에 정답 제출을 동시에 여러 번 보낸다.

**Then** 확정된 횟수 이상 점수가 증가하면 안 된다.

이 테스트를 통과할 DB 기록 구조가 먼저 필요하다.

---

## C-T17. WebSocket joined/ready/start — AFTER

각 DB 변경이 commit된 뒤에만 이벤트가 broadcast되는지 확인한다.

rollback된 변경은 이벤트로 전파되면 안 된다.

---

## C-T18. score_changed 최종값 — AFTER

이벤트가 단순 delta만이 아니라 서버의 최종 current_score를 제공해 중복 수신에도 UI가 복구 가능한지 확인한다.

---

## C-T19. 재접속 snapshot — AFTER

게임 중 socket을 끊고 다시 연결한다.

**Then** DB 기준으로 room status, participants, Ready, score, tasks가 복구되어야 한다.

---

## C-T20. 서버 재시작 후 재접속 — AFTER

connection manager 메모리가 사라져도 DB 상태로 복구 가능한지 확인한다.

현재 경기 진행 위치를 어디에 저장할지는 POLICY.

---

## C-T21. Finish 권한 — NOW

host + IN_PROGRESS에서만 FINISHED로 전환 가능.

---

## C-T22. 종료 조건/결과 계산 — AFTER/POLICY

자동 종료를 사용한다면 확정 조건에서만 FINISHED가 되고 순위/동점/팀 결과가 서버 기준으로 계산되어야 한다.

---

## C-T23. 결과 보상 1회성 — AFTER/POLICY

finish/result 처리 로직을 두 번 호출해도 재화가 두 번 지급되지 않아야 한다.

---

## C-T24. WebSocket 비참가자 연결 — AFTER

JWT는 유효하지만 ROOM_PARTICIPANTS에 없는 사용자의 socket 연결을 거절한다.

---

# C 완료 기준

```text
Lobby
→ 참가/Ready
→ Start 조건
→ 서버 채점
→ 중복 득점 방어
→ 점수 commit
→ WebSocket
→ 재접속
→ 결과/보상 1회성
```

까지 검증해야 실제 배틀 완료로 본다.
