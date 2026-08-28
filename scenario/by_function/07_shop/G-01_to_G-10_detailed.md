# G-01 ~ G-10. 상점 상세 시나리오

이 문서는 상점 진입, 상품 조회, 구매, 잔액 부족, 연타, 동일 상품 재구매, transaction rollback까지의 흐름을 정리한다.

> 상점 구매의 핵심 원칙은 **재화 차감에 FOR UPDATE를 사용하지 않고 DB Atomic Update를 사용한다**는 것이다.

---

# G-01. 상점 화면 진입

## 목적
사용자가 구매 가능한 상품 목록을 본다.

## 흐름
```text
상점 클릭
→ ITEMS 조회
→ 상품 id/category/name/price 반환
→ 프론트 상품 카드 렌더링
```

## DB 변경
없다.

## 주의
사용자의 현재 balance도 헤더에 필요하면 USERS 조회를 함께 하거나 기존 사용자 상태에서 사용한다.

## 테스트
- 상품 있음
- 상품 없음
- 여러 category

---

# G-02. 카테고리 필터

## 목적
가구, 벽지, 바닥 등을 사용자가 쉽게 나눠 본다.

## 방법 후보
1. 서버에 `?category=furniture`를 보내 필터링
2. 상품 수가 매우 적으면 전체를 받고 프론트에서 필터링

### 추천 MVP
데이터가 작아도 API 역할을 명확히 하고 싶다면 query parameter 필터를 지원하는 것이 좋다.

## DB
`ITEMS.category` 조건으로 SELECT.

## 주의
category 문자열 허용값을 팀에서 통일해야 오타 데이터가 생기지 않는다.

---

# G-03. 구매 확인 모달

## 목적
사용자가 실수로 상품을 누르자마자 결제되지 않게 한다.

## 흐름
```text
상품 클릭
→ 프론트가 name/price 표시
→ '구매하시겠습니까?'
→ 확인 시에만 POST 구매 API 호출
```

## 서버
모달에 표시된 가격을 신뢰하지 않는다. 구매 요청에서는 `item_id`만 받고 서버가 ITEMS.price를 다시 읽는다.

## 이유
사용자는 프론트의 가격 숫자를 조작할 수 있기 때문이다.

---

# G-04. 정상 구매

## Request 초안
JWT 이후:
```json
{
  "item_id": 5
}
```

## 처리 순서
```text
BEGIN
→ ITEMS에서 item_id/price 조회
→ USERS balance Atomic Update
→ 성공 여부 확인
→ INVENTORIES upsert
→ COMMIT
→ 현재 balance/item/quantity 반환
```

## Atomic Update
```sql
UPDATE users
SET balance = balance - :price
WHERE id = :user_id
  AND balance >= :price
RETURNING balance;
```

## Inventory
`(user_id,item_id)`가 없다면 quantity=1 INSERT, 이미 있다면 quantity를 증가시킨다.

## DB 제약
`INVENTORIES(user_id,item_id)` UNIQUE를 둬서 같은 사용자의 같은 item이 여러 row로 갈라지지 않게 한다.

---

# G-05. 잔액 부족

## 상황
상품 가격보다 balance가 작다.

## 처리
Atomic Update가 아무 row도 변경하지 않는다.

```text
affected rows = 0
→ INVENTORIES 수정하지 않음
→ rollback/종료
→ 409 Conflict
```

## 프론트
`재화가 부족합니다` 안내 후 구매 버튼을 다시 활성화한다.

## 테스트
- 가격보다 1 부족
- balance=0
- 정확히 가격만큼 있으면 성공

---

# G-06. 구매 버튼 연타

## 상황
사용자가 같은 상품 구매 API를 동시에 여러 번 호출한다.

## 프론트
첫 클릭 후 버튼을 비활성화하는 것이 UX상 좋다.

## 서버
프론트 방어만 믿지 않고 각 요청에서 Atomic Update의 `balance >= price`를 다시 평가한다.

## 예
현재 잔액이 상품 2개만 살 수 있는 금액이면 10개 요청이 와도 최대 2건만 차감 조건을 통과한다.

## FOR UPDATE를 쓰지 않는 이유
이 경우 필요한 작업은 '잔액을 조건에 따라 감소'시키는 단순 원자 연산이므로 DB UPDATE 자체에 맡기는 것이 더 단순하고 빠르다.

---

# G-07. 동일 상품 재구매

## 상황
사용자가 이미 캣타워를 1개 가지고 있는데 한 개 더 산다.

## 잘못된 구조
같은 `(user_id,item_id)` row를 매번 새로 INSERT하면 인벤토리 조회/수량 계산이 복잡해진다.

## 추천
```text
기존 row 없음 → INSERT quantity=1
기존 row 있음 → quantity=quantity+1
```

PostgreSQL upsert를 사용할 수 있다.

## 동시성
UNIQUE + upsert를 함께 사용하면 동시 재구매 시에도 동일 item의 소유 row가 하나로 유지되기 쉽다.

## 테스트
동일 item을 여러 번 구매해 row 수는 1이고 quantity만 증가하는지 확인한다.

---

# G-08. 존재하지 않는 상품 구매

## 상황
사용자가 가짜 item_id를 직접 전송한다.

## 처리
```text
ITEMS 조회
→ 없음
→ 404 Not Found
→ balance 차감 없음
```

## 중요한 순서
상품 존재와 가격을 먼저 확인한 다음 재화를 차감한다.

## 테스트
- 매우 큰 item_id
- 삭제/비활성 상품 개념을 도입한다면 판매 가능 여부 추가 검사 필요

---

# G-09. Inventory 저장 실패 시 rollback

## 상황
balance 차감은 성공했지만 INVENTORIES 처리 중 DB 오류가 발생한다.

## 절대 생기면 안 되는 상태
```text
돈은 빠짐
아이템은 없음
```

## 해결
balance 차감과 inventory 변경을 같은 transaction으로 묶는다.

```text
BEGIN
→ balance UPDATE
→ inventory upsert
→ ERROR
→ ROLLBACK
```

DB rollback이 balance 차감도 되돌린다.

## 테스트
테스트 환경에서 inventory 저장을 일부러 실패시켜 balance가 원래대로인지 확인한다.

---

# G-10. 구매 성공 후 UI 동기화

## 목적
성공 직후 프론트가 또 사용자 전체 정보를 요청하지 않아도 헤더 잔액과 보유 수량을 바로 갱신한다.

## Response 예시
```json
{
  "status": "success",
  "current_balance": 800,
  "item_id": 5,
  "item_name": "캣타워",
  "quantity": 2
}
```

## 화면
```text
구매 완료 토스트
→ 헤더 balance=800 갱신
→ 상품 보유 수량=2 갱신
```

## 왜 current_balance를 서버가 주나
프론트가 `기존 잔액 - 가격`을 직접 계산하면 동시에 다른 재화 변화가 있었을 때 화면이 실제 DB와 달라질 수 있다. DB가 확정한 최신 값을 반환하는 것이 안전하다.

---

# G 영역에서 팀이 확정/검토해야 할 것

1. ITEMS category 허용값
2. 판매 중지 상품을 위한 `is_active` 같은 컬럼이 필요한지
3. 구매 개수 1개 고정인지 수량 선택을 지원할지
4. 최대 보유 수량 제한이 있는지
5. 오류 HTTP status 통일
6. 인증 도입 후 body의 user_id 제거 시점
7. 상점 API prefix(`/api/v1` 등) 최종 규칙

현재 요구사항 기준 핵심 동시성 정책은 `Atomic Update + Inventory UNIQUE/upsert + 같은 transaction`이다.
