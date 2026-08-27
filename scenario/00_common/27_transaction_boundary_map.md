# 트랜잭션 경계 지도

이 문서는 각 쓰기 API에서 **어디부터 어디까지를 하나의 transaction으로 묶어야 하는지** 정리한다.

초보자 기준 핵심은 이것이다.

```text
서로 반드시 같이 성공해야 하는 DB 변경
→ 같은 transaction

중간 하나가 실패했을 때 앞의 변경도 취소되어야 함
→ rollback
```

---

# 1. 일반 문제 제출 접수

```text
POST /attempts
```

## transaction

```text
사용자 확인
→ TASK 확인
→ TASK_ATTEMPTS INSERT(PENDING)
→ COMMIT
```

여기서는 Docker 실행까지 같은 transaction으로 잡지 않는다.

이유:
- Docker는 오래 걸릴 수 있음
- DB transaction을 오래 열어두면 좋지 않음

따라서:

```text
접수 transaction 종료
→ 그 다음 BackgroundTask
```

으로 분리.

---

# 2. 채점 결과 저장

Docker 실행 후 별도 transaction.

```text
attempt 조회
→ 최종 status 결정
→ is_correct 변경
→ 보상/숙련도 필요 시 처리
→ COMMIT
```

보상을 같은 순간 지급한다면 결과 저장과 보상 사이에 중간 실패가 없도록 묶는 편이 좋다.

---

# 3. 최초 정답 보상

위험:
같은 문제의 두 attempt가 동시에 PASSED.

추천 검토:

```text
BEGIN
→ 사용자 row 짧게 FOR UPDATE
→ 과거 PASSED/보상 자격 재확인
→ attempt 최종화
→ 재화 증가
→ proficiency 변경
→ COMMIT
```

정확한 보상 정책 확정 후 구현.

---

# 4. 출석 체크

```text
BEGIN
→ ATTENDANCES INSERT
→ USERS 재화 증가
→ COMMIT
```

중간 재화 지급 실패:

```text
ROLLBACK
```

해야 한다.

그렇지 않으면 attendance만 기록되고 사용자는 보상을 못 받는다.

중복은 UNIQUE가 막는다.

---

# 5. 상점 구매

```text
BEGIN
→ ITEMS 가격 조회
→ USERS Atomic UPDATE(balance >= price)
→ INVENTORIES INSERT/upsert
→ COMMIT
```

Inventory 저장 실패:

```text
ROLLBACK
→ balance 차감도 취소
```

상점에서는 일반적으로 `FOR UPDATE`보다 조건부 Atomic UPDATE를 사용.

---

# 6. 가챠

```text
BEGIN
→ 가챠 비용 서버 기준 확인
→ USERS Atomic UPDATE
→ CATS 후보 추첨
→ USER_CATS INSERT 또는 중복 정책 처리
→ mileage 필요 시 변경
→ COMMIT
```

어느 단계라도 실패하면 전부 rollback.

```text
재화만 빠지고 고양이 없음
```

상태를 허용하지 않는다.

주의: 외부 API 호출이나 긴 애니메이션은 transaction 안에 넣지 않는다.

---

# 7. 배틀 방 생성

방장 자동 참가 정책을 채택한다면:

```text
BEGIN
→ ROOMS INSERT
→ ROOM_PARTICIPANTS(host) INSERT
→ COMMIT
```

같이 묶는 편이 자연스럽다.

자동 참가가 아니면 ROOMS INSERT만.

---

# 8. 방 입장

대표 FOR UPDATE 시나리오.

```text
BEGIN
→ SELECT ROOMS ... FOR UPDATE
→ WAITING 확인
→ 중복 참가 확인
→ participant count
→ max_participants 비교
→ ROOM_PARTICIPANTS INSERT
→ COMMIT
```

lock은 commit과 함께 해제된다.

---

# 9. Ready 변경

```text
BEGIN
→ room WAITING 확인
→ participant ownership 확인
→ is_ready UPDATE
→ COMMIT
```

단순 row update라 긴 lock은 필요 없음.

WebSocket broadcast는 DB commit 이후 보내는 편이 안전하다.

왜냐하면 DB가 rollback됐는데 먼저 `READY=true` 이벤트를 방송하면 화면과 DB가 어긋날 수 있기 때문이다.

---

# 10. 배틀 시작

```text
BEGIN
→ room/host 확인
→ 필요 시 room row lock
→ 최소 인원 확인
→ Ready 규칙 확인
→ ROOM_TASKS 확인
→ ROOMS.status = IN_PROGRESS
→ COMMIT
```

그 다음:

```text
WebSocket game_start broadcast
```

---

# 11. 배틀 점수 증가

프론트가 점수를 보내는 게 아니라 서버 채점 결과가 기준.

```text
채점 PASSED
→ BEGIN
→ 해당 participant/problem 중복 득점 여부 확인
→ current_score 증가
→ COMMIT
→ WebSocket score_update
```

현재 ERD에는 사용자별 '이 방의 이 문제를 이미 득점했는지' 별도 테이블이 없다.

따라서 중복 득점 방지 방법은 추가 설계 필요.

---

# 12. 배틀 종료 + 보상

이상적인 형태:

```text
BEGIN
→ room IN_PROGRESS 확인
→ 최종 점수 계산
→ 승자 결정
→ room FINISHED
→ 보상 1회 지급 여부 확인
→ USERS 재화 지급
→ COMMIT
```

하지만 현재 ERD에 보상 지급 완료 플래그/이력이 없다.

따라서 이 transaction을 안전하게 만들려면 보상 중복 방지 구조부터 결정해야 한다.

---

# 13. 승급전 시작

```text
BEGIN
→ ranking participant 확인
→ active challenge 없음 확인
→ RANK_CHALLENGES INSERT
→ RANK_CHALLENGE_TASKS 여러 행 INSERT
→ COMMIT
```

challenge만 생기고 task가 하나도 없는 상태를 막기 위해 같이 묶는다.

---

# 14. 승급전 코드 저장

```text
BEGIN
→ challenge ownership 확인
→ IN_PROGRESS 확인
→ now < expires_at 확인
→ saved_code UPDATE
→ COMMIT
```

단순 update.

---

# 15. 승급전 문제 통과

```text
채점 결과 PASSED
→ BEGIN
→ challenge 상태/만료 재확인
→ RANK_CHALLENGE_TASKS.is_passed = true
→ 전체 합격 여부 확인
→ 필요 시 challenge SUCCESS 전환
→ rank score / 보상 처리
→ COMMIT
```

성공 보상이 있다면 `IN_PROGRESS → SUCCESS` 최초 전환 transaction 안에서 같이 지급하는 게 중복 방지에 유리하다.

---

# 16. 승급전 TIMEOUT

사용자가 페이지를 열어둔다고 서버 timer thread를 꼭 계속 돌릴 필요는 없다.

API 요청 시:

```text
now >= expires_at
AND status == IN_PROGRESS
```

이면:

```text
BEGIN
→ status = TIMEOUT
→ COMMIT
```

으로 확정 가능.

필요하면 별도 정리 job을 둘 수 있다.

---

# 17. 가구 배치

```text
BEGIN
→ Inventory 소유량 확인
→ 동일 item 배치 개수 확인
→ category 확인
→ PLACED_OBJECTS INSERT
→ COMMIT
```

동시에 같은 아이템을 여러 번 배치하면 quantity 초과 race가 생길 수 있다.

엄격히 막으려면 해당 사용자 inventory row를 짧게 lock하는 방법을 검토한다.

---

# 18. 가구 이동/삭제

이동:

```text
BEGIN
→ ownership 확인
→ position_data UPDATE
→ COMMIT
```

삭제:

```text
BEGIN
→ ownership 확인
→ PLACED_OBJECTS DELETE
→ COMMIT
```

Inventory quantity는 변경하지 않는다.

---

# 19. 벽지/바닥 적용

```text
BEGIN
→ Inventory 소유 확인
→ ITEMS.category 확인
→ USERS.wallpaper_item_id 또는 floor_item_id UPDATE
→ COMMIT
```

---

# Transaction 안에 넣지 말아야 할 것

가능하면 다음은 DB transaction 밖에서 처리한다.

- 긴 Docker 실행
- 프론트 애니메이션 대기
- 외부 LLM API 호출
- WebSocket 전송 대기
- sleep
- 오래 걸리는 파일 처리

DB lock을 오래 잡으면 다른 요청이 불필요하게 기다린다.

---

# Commit 후 이벤트 원칙

실시간 이벤트는 가능하면:

```text
DB COMMIT 성공
→ WebSocket broadcast
```

순서.

반대로:

```text
broadcast
→ DB commit 실패
```

하면 사용자 화면은 성공으로 보지만 DB는 실패한 상태가 될 수 있다.

---

# 공통 체크리스트

쓰기 API마다 아래를 적는다.

```text
[ ] transaction 시작 지점
[ ] commit 지점
[ ] rollback 조건
[ ] FOR UPDATE 필요한가?
[ ] UNIQUE로 해결 가능한가?
[ ] Atomic Update가 가능한가?
[ ] 외부 작업을 transaction 안에서 오래 기다리고 있지 않은가?
[ ] 같은 요청 두 번 실행 시 안전한가?
[ ] commit 후 프론트/WebSocket 이벤트를 보내는가?
```

이 지도를 기준으로 실제 구현 코드를 리뷰한다.
