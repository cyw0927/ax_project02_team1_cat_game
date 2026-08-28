# 05. 인벤토리 반영

## 목적
구매가 성공한 뒤 구매한 아이템을 사용자 인벤토리에 정확히 반영하고, 같은 구매 요청이 중복 처리되거나 동시 요청이 겹쳐도 수량이 꼬이지 않도록 한다.

## 정상 흐름
1. `04_atomic_purchase.md`에서 잔액 차감 조건이 성공한다.
2. 같은 짧은 트랜잭션 안에서 INVENTORIES를 갱신한다.
3. `(user_id, item_id)`가 이미 있으면 quantity를 증가시킨다.
4. 없으면 새 inventory row를 만든다.
5. 잔액 차감과 inventory 변경이 모두 성공해야 commit 한다.
6. 서버는 최신 balance와 해당 item quantity를 반환한다.

## 발생 가능한 변수

### A. 해당 아이템 inventory row가 이미 존재
- 원인: 이전 구매 이력 있음.
- 해결: 중복 row를 새로 만들지 않고 기존 quantity 증가.
- DB: `(user_id, item_id)` UNIQUE를 기준으로 UPSERT 사용 가능.

### B. 두 기기에서 같은 아이템을 동시에 구매
- 위험: read → quantity+1 → save 방식이면 한 번 증가분이 사라지는 lost update 가능.
- 해결: DB 원자 증가 또는 UPSERT의 `quantity = inventories.quantity + excluded.quantity` 같은 방식 우선.

### C. 잔액 차감 성공 후 inventory 갱신 실패
- 원인: DB 오류, 제약 위반, 연결 문제.
- 해결: 둘을 같은 트랜잭션으로 묶어 전체 rollback. 돈만 빠지고 아이템이 없는 상태를 만들지 않는다.

### D. inventory는 증가했는데 응답 유실
- 원인: commit 후 네트워크 끊김.
- 위험: 사용자가 실패로 착각하고 재구매.
- 해결: 구매 API의 멱등 정책이 필요할 수 있다. 현재 범용 purchase ledger가 확정돼 있지 않다면 `TBD`로 둔다.

### E. quantity가 비정상 값
- 원인: 과거 데이터 오류, 잘못된 마이그레이션.
- 감지: 음수/NULL 등 정책상 불가능한 값 검증.
- 해결: 비정상 row를 정상 구매 결과처럼 덮어쓰지 말고 오류 로깅 및 데이터 복구 대상으로 분리.

## UI
- 구매 완료 시 최신 보유 수량 표시.
- 응답 실패 시 프론트에서 임의로 quantity를 +1 하지 않고 서버 재조회.
- 이미 보유 중인 가구라면 `보유 2개`처럼 수량 표시 가능.

## DB/API 영향
- INVENTORIES(user_id, item_id, quantity)
- USERS.balance
- 구매 성공 응답에 최신 balance와 quantity 포함 권장.

## 동시성 원칙
- 장시간 lock 금지.
- 잔액 조건부 차감 + inventory 원자 증가를 짧은 트랜잭션으로 처리.
- 프론트 버튼 disabled는 UX일 뿐 정합성 보호 수단이 아니다.

## 다음 단계 조건
- inventory 반영 성공 → `07_purchase_complete.md`
- 중간 실패 → `06_failure_rollback.md`

## 테스트
- 첫 구매
- 같은 아이템 재구매
- 두 기기 동시 구매
- inventory UPSERT 충돌
- 잔액 차감 후 inventory 실패
- commit 후 응답 유실
- 비정상 quantity 데이터
