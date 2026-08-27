# DB 동시성·트랜잭션 공통 규칙

동시 요청이 들어온다고 무조건 `FOR UPDATE`를 쓰는 것이 아니다. 상황에 맞는 가장 단순한 방어 방법을 선택한다.

## 1. 재화 차감: DB Atomic Update

대표 기능:
- 상점 구매
- 가챠 비용 차감

권장 개념:

```sql
UPDATE users
SET balance = balance - :amount
WHERE id = :user_id
  AND balance >= :amount;
```

업데이트된 행이 1개면 성공, 0개면 잔액 부족이다.

### 왜 좋은가

파이썬에서 잔액을 읽고 계산한 뒤 저장하면 동시에 여러 요청이 같은 이전 잔액을 읽는 문제가 생길 수 있다. DB가 조건 검사와 차감을 한 문장으로 처리하게 하면 이 위험을 크게 줄일 수 있다.

### 주의

재화 차감만 성공하고 아이템 저장이 실패하면 안 된다. 따라서 상점/가챠에서는 차감과 소유권 저장을 **같은 transaction**으로 묶는다.

---

## 2. 여러 상태를 읽고 판단: SELECT ... FOR UPDATE

대표 기능:
- 배틀 방 입장
- 필요하다면 최초 정답 보상 확정 구간

방 입장 예:

```text
ROOM row FOR UPDATE
→ room.status 확인
→ 참가자 수 확인
→ 정원 확인
→ participant INSERT
→ COMMIT
```

첫 요청이 commit할 때까지 두 번째 요청은 같은 방 row에서 기다리므로 마지막 자리 경쟁을 직렬화할 수 있다.

### 주의

락을 잡은 상태에서 Docker 실행, 외부 API 호출, 긴 계산을 하지 않는다. lock 구간은 최대한 짧게 유지한다.

---

## 3. '중복 자체가 금지'인 경우: UNIQUE

대표 기능:
- 하루 1회 출석: `(user_id, check_in_date)`
- 인벤토리 한 사용자/아이템 한 행: `(user_id, item_id)`
- 방 중복 참가: `(room_id, user_id)`
- 방 문제 순서 중복 방지 등

서버 코드에서 `SELECT → 없으면 INSERT`만 믿기보다 DB UNIQUE가 마지막 방어벽이 되어야 한다.

중복 INSERT가 들어오면 `IntegrityError`를 잡아 의미 있는 API 오류로 변환한다.

---

## 4. Transaction이 필요한 대표 흐름

### 상점

```text
ITEM 가격 조회
→ balance Atomic Update
→ INVENTORY upsert
→ COMMIT
```

중간 실패 시 전부 rollback.

### 가챠

```text
비용 차감
→ 추첨
→ USER_CATS/마일리지 반영
→ COMMIT
```

추첨 결과 저장 실패 시 비용도 rollback되어야 한다.

### 출석

```text
ATTENDANCE INSERT
→ balance 보상 반영
→ COMMIT
```

보상 실패 시 출석만 남지 않도록 같은 transaction으로 처리하는 방향이 안전하다.

---

## 5. 프론트 버튼 잠금은 DB 방어가 아니다

버튼을 비활성화하면 일반 사용자의 연타를 줄일 수 있지만, 사용자는 API를 직접 호출할 수 있다.

따라서:

```text
프론트 버튼 비활성화 = UX
DB Atomic/Lock/UNIQUE = 실제 정합성 방어
```

두 역할을 구분한다.

---

## 6. 초보자용 선택 기준

```text
숫자 하나를 조건부로 바꾸는가?
→ Atomic Update

현재 여러 상태를 읽고 다음 행동을 결정해야 하는가?
→ 필요한 row에 FOR UPDATE 검토

똑같은 조합이 애초에 두 번 존재하면 안 되는가?
→ UNIQUE
```

한 기능에 두 방법이 같이 필요할 수도 있다. 예를 들어 상점은 balance Atomic Update와 Inventory UNIQUE/upsert를 동시에 사용할 수 있다.