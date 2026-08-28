# G. 상점 DB Before / After

이 문서는 상점 구매에서 **USERS.balance와 INVENTORIES.quantity가 어떻게 같이 바뀌는지** 정리한다.

현재 1개 구매 핵심 transaction은 구현돼 있다.

재화 종류·다수 구매·판매중지·환불은 확정 전 임의로 넣지 않는다.

---

## G-DB01. 아이템 목록 조회 — 현재

### Before

`ITEMS`에 상품들이 존재.

### API

```http
GET /items
```

### After

DB 변화 없음.

현재는 모든 item을 반환한다.

---

## G-DB02. Inventory 조회 — 현재

### Before

```text
INVENTORIES
U1/I10 quantity=2
U1/I20 quantity=1
U2/I10 quantity=5
```

### API

```http
GET /users/U1/inventory
```

### After

DB 변화 없음.

U1 데이터만 반환한다.

---

## G-DB03. 정상 첫 구매 — 현재

### Before 예시

```text
USERS.U1.balance = 1000
ITEMS.I10.price = 300
INVENTORIES에 U1/I10 없음
```

### 처리

```text
BEGIN
→ User 확인
→ Item 확인
→ 서버 ITEMS.price 사용
→ USERS 조건부 Atomic UPDATE
→ INVENTORIES INSERT quantity=1
→ COMMIT
```

### After

```text
USERS.U1.balance = 700
INVENTORIES U1/I10 quantity=1
```

예시 숫자는 흐름 설명용이며 실제 가격은 DB `ITEMS.price` 값이다.

---

## G-DB04. 동일 아이템 재구매 — 현재

### Before

```text
USERS.U1.balance = 충분
INVENTORIES U1/I10 quantity=1
```

### 처리

재화 차감 후 PostgreSQL upsert.

### After

```text
INVENTORIES U1/I10 quantity=2
```

새 중복 Inventory row를 만들지 않는다.

최종 방어:

```text
UNIQUE(user_id, item_id)
```

---

## G-DB05. 잔액 부족 — 현재

### Before

```text
USERS.U1.balance < ITEMS.I10.price
```

### 핵심 SQL 개념

```sql
UPDATE users
SET balance = balance - :price
WHERE id = :user_id
  AND balance >= :price;
```

조건을 만족하지 않아 update row가 없음.

### After

```text
balance 변화 없음
Inventory 변화 없음
```

---

## G-DB06. 동시에 여러 구매 — 현재 핵심 동시성

### Before

잔액이 한 개만 살 수 있을 정도라고 가정.

여러 요청이 동시에 들어온다.

### 처리

각 요청의 조건부 UPDATE가 DB에서 경쟁한다.

### After 목표

```text
성공 구매 수 <= 실제 잔액으로 살 수 있는 수
balance >= 0
Inventory 증가량 = 성공 구매 수
```

Python에서 balance를 읽고 계산해 덮어쓰는 방식보다 안전하다.

---

## G-DB07. Inventory 저장 실패 rollback

### transaction 중

```text
balance 차감 성공
→ Inventory upsert 실패
```

### 처리

```text
ROLLBACK
```

### After

```text
USERS.balance = Before와 동일
INVENTORIES = Before와 동일
```

사용자가 돈만 잃지 않아야 한다.

---

## G-DB08. 존재하지 않는 item

### Before

요청 item_id가 `ITEMS`에 없음.

### After

```text
balance 변화 없음
Inventory 변화 없음
```

가격을 프론트가 보내더라도 없는 item을 임의로 구매시키지 않는다.

---

## G-DB09. 프론트 가격 위조

현재 Request에는 price 자체가 없다.

### Before

```text
ITEMS.I10.price = 서버 값
```

### 처리

서버가 해당 값을 읽어 차감.

### After

프론트가 화면 값을 조작해도 차감액은 서버 DB 가격 기준이어야 한다.

---

## G-DB10. 구매 Response와 DB 동기화

### After commit

Response의:

```text
current_balance
quantity
```

는 실제 DB 값과 같아야 한다.

프론트는 이 최종값으로 HUD를 갱신한다.

---

## G-DB11. 네트워크 중복 요청

현재 각 성공 Request는 별도 정상 구매로 처리된다.

만약 같은 요청 재전송을 한 번만 인정하기로 하면 idempotency 구조를 추가 검토한다.

### 목표 After 후보

같은 idempotency key 두 번:

```text
balance 차감 1회
Inventory 증가 1회
```

실제 사용자의 두 번 구매와는 구분한다.

---

## G-DB12. 다수 구매 — 정책 미정

quantity 기반 구매를 넣는다면:

### 처리 후보

```text
총액 = 서버 item.price × 요청 quantity
→ 조건부 Atomic 차감
→ Inventory.quantity += quantity
→ COMMIT
```

### After

```text
balance = Before - 총액
Inventory = Before + quantity
```

중간 실패 시 둘 다 rollback.

---

## G-DB13. 판매중지 — 스키마 정책 미정

현재 ITEMS에는 `is_active`가 없다.

향후 추가한다면:

```text
기존 INVENTORIES는 그대로 유지
신규 구매만 거절
```

해야 한다.

이미 소유한 아이템을 판매중지 때문에 삭제하지 않는다.

---

## G-DB14. 다중 재화 — 정책 미정

현재 상점은 `USERS.balance`를 차감한다.

향후 일반/고급 재화를 확정하면:

```text
어떤 item이 어떤 재화를 사용하는지
어느 USERS 컬럼을 Atomic UPDATE하는지
```

를 함께 변경한다.

기획 확정 전에 컬럼을 임의로 추가하지 않는다.

---

## G-DB15. JWT ownership

### 공격

JWT U1이 Request에 U2의 user_id를 넣음.

### After 목표

```text
U2.balance 변화 없음
U2.Inventory 변화 없음
```

최종 구매는 인증된 U1을 기준으로 한다.

---

# 한눈에 보는 핵심

```text
구매 성공
서버 가격 조회
→ Atomic balance 차감
→ Inventory upsert
→ COMMIT

잔액 부족
Atomic UPDATE 0 row
→ Inventory 변화 없음

중간 실패
ROLLBACK
→ 돈과 아이템 둘 다 Before 상태
```

상점 DB의 핵심은 **잔액이 절대 음수가 되지 않고, 재화 차감과 아이템 지급이 항상 같이 성공하거나 같이 실패하는 것**이다.
