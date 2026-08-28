# 04. 원자적 재화 차감 및 인벤토리 반영

## 목적
재화 차감과 아이템 지급을 하나의 짧은 DB 트랜잭션으로 처리해 `돈만 빠짐` 또는 `아이템만 늘어남` 같은 불일치를 막는다.

## 정상 흐름
1. 서버가 현재 item price를 확정한다.
2. 조건부 원자 UPDATE로 잔액 차감을 시도한다.
3. 영향 row가 1이면 잔액 차감 성공으로 본다.
4. INVENTORIES에 해당 item row가 없으면 생성하고, 있으면 quantity를 증가시킨다.
5. 두 변경이 모두 성공하면 commit한다.
6. 하나라도 실패하면 전체 rollback한다.

## 권장 재화 차감 방식
```sql
UPDATE users
SET balance = balance - :price
WHERE id = :user_id
  AND balance >= :price;
```

영향 row가 0이면 잔액 부족 또는 사용자 상태 문제로 처리한다.

## 발생 가능한 변수
### A. 동시에 두 구매 요청
- 예: 잔액 100, 각 상품 가격 80.
- 단순 read-modify-write면 둘 다 성공처럼 보일 수 있다.
- 조건부 UPDATE를 사용하면 먼저 성공한 거래 후 두 번째는 조건 실패한다.

### B. 차감 성공 후 inventory 증가 실패
- 원인: DB 오류, 제약 위반.
- 해결: 같은 transaction이면 전체 rollback.

### C. inventory row 중복 생성 경쟁
- `(user_id, item_id)` UNIQUE를 전제로 UPSERT를 사용하면 동시 생성 충돌을 줄일 수 있다.

### D. transaction 중 서버 예외
- commit 전 예외면 rollback.
- commit 여부가 불명확하면 다음 단계에서 서버 상태를 재조회한다.

### E. 불필요한 row lock 확대
- 단순 잔액 차감은 가능한 한 조건부 UPDATE로 처리하고, 장시간 `FOR UPDATE`를 잡지 않는다.

## DB 영향
- USERS.balance 감소
- INVENTORIES.quantity 증가 또는 row 생성

## 트랜잭션 원칙
- 외부 API 호출이나 긴 작업을 transaction 안에 넣지 않는다.
- 거래는 짧게 끝낸다.
- 실패 시 일부 변경만 commit되지 않도록 한다.

## UI
거래 transaction이 끝나기 전 프론트에서 잔액이나 보유 수량을 확정값처럼 먼저 증가/감소시키지 않는다.

## 다음 단계 조건
commit 성공 → `05_purchase_result.md`
rollback/조건 실패 → `06_failure_retry.md`

## 테스트
- 정상 구매
- 잔액 정확히 가격과 동일
- 잔액 부족
- 동시 구매 2건
- inventory 기존 row
- inventory 신규 row
- inventory 처리 중 DB 오류
- transaction rollback

## TBD
- bulk quantity 구매
- 최대 보유량 제약