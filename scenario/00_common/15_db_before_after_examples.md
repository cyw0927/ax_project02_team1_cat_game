# DB 변경 Before / After 예시

초보자가 API가 실제 DB에 어떤 변화를 만드는지 이해하기 위한 예시다. 숫자 보상/가격은 예시값일 수 있으며 확정 규칙이 아니다.

## 1. 문제 제출

### Before
`TASK_ATTEMPTS`에 해당 제출 없음.

### 처리
```text
POST /attempts
→ 사용자/문제 확인
→ 새 attempt INSERT
```

### After
```text
TASK_ATTEMPTS
id: A1
user_id: U1
task_id: T1
status: PENDING
is_correct: false
used_hint: false
submitted_code: ...
```

채점 후에는 같은 row의 `status`, `is_correct`를 변경한다. 재제출은 기존 row를 덮어쓰지 않고 새 row를 만든다.

---

## 2. 최초 정답 보상

### Before
```text
USERS U1 balance = 500
TASK_ATTEMPTS: T1에 대한 과거 PASSED 없음
```

### 처리
```text
채점 PASSED
→ 과거 최초 정답 여부 검사
→ 최초라면 보상
```

### After 예시
```text
TASK_ATTEMPTS A1 status = PASSED
TASK_ATTEMPTS A1 is_correct = true
USERS U1 balance = 500 + 기획 확정 보상
```

같은 문제를 다시 정답 처리했을 때는 attempt는 추가되지만 최초 보상은 다시 지급하지 않는다.

---

## 3. 상점 구매

### Before
```text
USERS U1 balance = 300
ITEMS I5 price = 200
INVENTORIES (U1,I5) 없음
```

### 처리
```sql
UPDATE users
SET balance = balance - 200
WHERE id = U1 AND balance >= 200;
```

성공하면 Inventory upsert.

### After
```text
USERS U1 balance = 100
INVENTORIES
user_id = U1
item_id = I5
quantity = 1
```

동일 아이템을 다시 사면 새 Inventory row를 만들기보다 quantity를 증가시킨다.

---

## 4. 출석 체크

### Before
```text
오늘 날짜 ATTENDANCES(U1, today) 없음
```

### 처리
```text
ATTENDANCES INSERT
→ 성공한 경우 streak 계산
→ 보상 반영
→ 같은 transaction commit
```

### After
```text
ATTENDANCES
user_id = U1
check_in_date = today
streak_count = N
```

같은 날 두 번째 요청은 `(user_id, check_in_date)` UNIQUE 때문에 실패한다.

---

## 5. 방 입장

### Before
```text
ROOMS R1
status = WAITING
max_participants = 4

ROOM_PARTICIPANTS R1 = 3명
```

### 처리
```text
ROOMS R1 SELECT ... FOR UPDATE
→ 참가자 수 확인
→ 3 < 4
→ participant INSERT
→ commit
```

### After
```text
ROOM_PARTICIPANTS R1 = 4명
```

동시에 들어온 다음 요청은 lock이 풀린 뒤 4명을 확인하고 입장 실패한다.

---

## 6. 배틀 Ready

### Before
```text
ROOM_PARTICIPANTS P1
is_ready = false
```

### After
```text
ROOM_PARTICIPANTS P1
is_ready = true
```

ROOM이 WAITING이 아닐 경우 변경하지 않는다.

---

## 7. 배틀 점수

### Before
```text
ROOM_PARTICIPANTS P1 current_score = 200
```

정답 판정 후 기획 확정 점수만큼 증가.

### After 예시
```text
ROOM_PARTICIPANTS P1 current_score = 200 + 정답 점수
```

점수 저장과 실시간 WebSocket 전송은 구분한다. DB가 최종 기준이고 WebSocket은 화면 동기화 수단이다.

---

## 8. 승급전 시작

### Before
진행 중인 challenge 없음.

### After
```text
RANK_CHALLENGES
id = C1
user_id = U1
status = IN_PROGRESS
started_at = server_now
expires_at = server_now + 기획 확정 제한시간

RANK_CHALLENGE_TASKS
C1-T1 order 1
C1-T2 order 2
...
```

한 사용자가 동시에 여러 IN_PROGRESS challenge를 만들지 못하게 방어한다.

---

## 9. 승급전 코드 저장

### Before
```text
RANK_CHALLENGE_TASKS.saved_code = null 또는 이전 코드
```

### After
```text
saved_code = 현재 편집 중인 코드
```

점수/합격 여부는 코드 자동저장만으로 변경하지 않는다.

---

## 10. 가구 배치

### Before
```text
INVENTORIES(U1,I5).quantity = 2
PLACED_OBJECTS에서 I5 배치 = 1개
```

### 처리
보유 수량과 이미 배치한 수량을 확인한 뒤 새 배치 row 생성.

### After
```text
PLACED_OBJECTS
id = O2
user_id = U1
item_id = I5
position_data = {x,y,rotation...}
```

Inventory 수량 자체는 줄이지 않는다. `소유 개수`와 `현재 방에 배치된 개수`를 비교한다.

---

## 11. 가구 치우기

### Before
PLACED_OBJECTS O2 존재.

### After
O2 삭제.

INVENTORIES quantity는 그대로이므로 다시 배치할 수 있다.

---

## 12. 가챠

### Before
```text
USERS U1 = 가챠 비용 이상 재화 보유
USER_CATS에 결과 고양이 없음(또는 중복 가능)
```

### 처리
```text
재화 Atomic Update
→ 추첨
→ USER_CATS 저장 또는 중복 정책 처리
→ 모두 성공하면 commit
```

### After
```text
USERS 재화 감소
USER_CATS 새 row 또는 중복 정책에 따른 mileage 등 변경
```

중간에 저장 실패하면 재화 차감까지 rollback해야 한다.

## 핵심 기억

- 조회 API는 보통 Before/After가 같다.
- INSERT는 이력/소유권을 새로 만든다.
- UPDATE는 상태/점수/재화를 바꾼다.
- DELETE는 하우징에서 '치우기'처럼 의미를 정확히 구분한다.
- 한 기능에서 여러 테이블이 바뀌면 어느 지점까지 하나의 transaction인지 반드시 정한다.
