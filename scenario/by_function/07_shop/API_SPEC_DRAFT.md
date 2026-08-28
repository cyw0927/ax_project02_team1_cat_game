# G. 상점 API 명세 초안

이 문서는 `07_shop` 시나리오를 실제 API 계약으로 옮기기 위한 초안이다.

현재 `main`에는 아이템 목록, 1개 구매, 사용자 Inventory 조회가 구현돼 있다. 구매는 PostgreSQL Atomic UPDATE와 Inventory upsert를 사용한다.

재화 종류, 다수 구매, 판매중지, 환불은 아직 정책 미정이므로 임의로 확정하지 않는다.

---

## 1. 아이템 목록

### Endpoint

```http
GET /items
```

### 현재 구현

구현됨.

### Response

```json
[
  {
    "id": 10,
    "category": "furniture",
    "name": "...",
    "price": 100
  }
]
```

### DB

- `ITEMS` Read

### 남음

현재는 전체 item을 반환한다.

필요해지면:

```text
category filter
pagination
판매중지 item 제외
```

를 추가한다.

---

## 2. 카테고리 필터

### Endpoint 후보

```http
GET /items?category=furniture
```

### 현재 상태

미구현.

실제 화면에서 필터가 필요한지 확인 후 추가한다.

서버는 허용 category 값을 검증하고 임의 SQL 문자열을 그대로 조합하지 않는다.

---

## 3. 사용자 Inventory

### Endpoint

```http
GET /users/{user_id}/inventory
```

### 현재 구현

구현됨.

### Response

```json
[
  {
    "item_id": 10,
    "category": "furniture",
    "name": "...",
    "price": 100,
    "quantity": 2
  }
]
```

JWT 도입 후 본인 Inventory는:

```http
GET /me/inventory
```

형태를 검토할 수 있다.

---

## 4. 1개 구매

### Endpoint

```http
POST /shop/buy
```

### 현재 Request

```json
{
  "user_id": "user-uuid",
  "item_id": 10
}
```

### JWT 적용 후 후보

```json
{
  "item_id": 10
}
```

사용자는 JWT에서 식별한다.

---

## 5. 구매 처리 순서

현재 구현은 다음 흐름이다.

```text
User 존재 확인
→ Item 존재 확인
→ 서버 Item.price 사용
→ USERS 조건부 Atomic UPDATE
→ INVENTORIES upsert
→ COMMIT
```

핵심 SQL 개념:

```sql
UPDATE users
SET balance = balance - :price
WHERE id = :user_id
  AND balance >= :price
RETURNING balance;
```

### 의미

프론트가 보내는 가격을 믿지 않는다.

잔액 부족이면 UPDATE 대상 row가 없으므로 구매를 중단한다.

---

## 6. 구매 성공 Response

현재 Response:

```json
{
  "status": "success",
  "current_balance": 900,
  "item_id": 10,
  "item_name": "...",
  "quantity": 2
}
```

프론트는 성공 후 별도 전체 새로고침 없이 이 최종값으로 HUD와 Inventory를 갱신할 수 있다.

---

## 7. 잔액 부족

### 상태코드

현재:

```http
409 Conflict
```

### Response

```json
{
  "detail": "Insufficient balance"
}
```

### DB 결과

```text
balance 변화 없음
Inventory 변화 없음
```

이어야 한다.

---

## 8. 동일 아이템 재구매

현재 `INVENTORIES(user_id, item_id)` UNIQUE를 이용해 PostgreSQL upsert를 한다.

```text
처음 구매
→ INSERT quantity=1

이미 보유
→ quantity = quantity + 1
```

따라서 동일 item을 여러 번 정상 구매하는 것은 현재 구조에서 지원된다.

---

## 9. transaction rollback

다음 상태를 허용하면 안 된다.

```text
balance 차감 성공
→ Inventory 저장 실패
→ COMMIT
```

현재는 balance 차감과 Inventory upsert가 같은 DB session/transaction 안에 있고 마지막에 commit한다.

중간에 Inventory 저장이 실패하면 rollback되어 balance 차감도 취소되어야 한다.

자동 테스트로 반드시 확인한다.

---

## 10. 버튼 연타

상점에서는 두 가지를 구분해야 한다.

```text
사용자가 진짜 3개 사고 싶어서 3회 구매
vs
같은 네트워크 요청이 재전송됨
```

현재 API는 각 성공 요청을 독립 구매로 처리한다.

네트워크 중복 요청을 한 번만 인정해야 한다면 향후 idempotency key를 검토한다.

프론트 버튼 잠금은 UX 보조일 뿐 잔액 음수 방어는 Atomic UPDATE가 담당한다.

---

## 11. 다수 구매

### 현재 상태

미구현 / 정책 미정.

후보 Request:

```json
{
  "item_id": 10,
  "quantity": 3
}
```

하지만 실제 요구가 없다면 1개 구매 API를 반복 사용하는 것으로 MVP를 단순화할 수 있다.

다수 구매를 넣는다면 서버가:

```text
총 가격 = item.price × quantity
```

를 계산한다.

---

## 12. 판매중지

현재 ITEMS에는 `is_active`가 없다.

이미 Inventory에서 참조 중인 item을 물리 삭제하지 않고 신규 판매만 막고 싶다면:

```text
ITEMS.is_active
```

같은 컬럼을 검토할 수 있다.

현재는 **POLICY / SCHEMA GAP**.

---

## 13. 재화 구조 변경

현재 구매는 `USERS.balance` 하나를 사용한다.

향후 일반 재화/고급 재화가 최종 확정되면 다음을 같이 바꿔야 한다.

```text
ITEMS가 어떤 재화로 가격을 표시하는지
구매 Atomic UPDATE 대상 컬럼
Response의 잔액 필드
프론트 HUD
seed/test 데이터
```

재화 정책 확정 전에 임의로 `feed_balance`, `gold_balance` 등을 코드에 만들지 않는다.

---

## 14. 환불

### 현재 상태

미구현 / 정책 미정.

MVP에서 제외 가능하다.

환불을 넣는다면 이미 하우스에 배치한 item, 수량, 재화 반환 기준까지 같이 설계해야 하므로 단순 DELETE API로 만들지 않는다.

---

## 15. JWT ownership

최종적으로 구매/내 Inventory 조회는 JWT 사용자를 기준으로 한다.

프론트가 다른 사람 `user_id`를 넣어:

```text
남의 balance 차감
남의 Inventory 증가
```

시키는 구조가 남으면 안 된다.

---

# G 영역 완료 판정

```text
아이템 목록                 DONE
Inventory 조회              DONE
1개 구매                    DONE
서버 가격 기준              DONE
Atomic 차감                 DONE
Inventory upsert            DONE
rollback 구조               DONE(테스트 필요)
category filter             MISSING
다수 구매                   POLICY
판매중지                    POLICY/SCHEMA GAP
환불                        POLICY
JWT 사용자 식별            MISSING
다중 재화                   POLICY
```

# 구현 전 핵심 결정

1. 최종 재화 구조
2. 어떤 category를 상점에서 파는지
3. 판매중지 필요 여부
4. 다수 구매 필요 여부
5. 환불 MVP 포함 여부
6. idempotency key 필요 여부
7. JWT 전환 시 Request에서 user_id 제거 시점

현재 상점 핵심 transaction은 이미 비교적 완성도가 높으므로, 기획이 확정되기 전 불필요하게 다시 갈아엎지 않는다.
