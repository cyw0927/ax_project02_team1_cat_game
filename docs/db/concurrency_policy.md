# DB Concurrency & Lock Policy

## 기본 원칙

DB는 상태 저장과 원자성 보장을 담당하고, 장시간 작업과 실행 동시성 제어는 애플리케이션/Docker 계층에서 처리합니다.

1. 명시적 DB lock은 최소화합니다.
2. 조건부 `UPDATE`로 해결 가능한 경우 `SELECT ... FOR UPDATE`를 사용하지 않습니다.
3. 중복 방지는 가능하면 `UNIQUE` 제약조건과 idempotent write를 우선합니다.
4. Docker 실행, 외부 I/O, 장시간 계산 중 DB transaction을 유지하지 않습니다.
5. `FOR UPDATE`는 복수 조건 상태 전이를 반드시 직렬화해야 할 때만 사용합니다.
6. lock은 가능한 한 row 단위, transaction은 가능한 한 짧게 유지합니다.
7. Docker 동시 실행 제어는 DB lock이 아니라 application semaphore/queue가 담당합니다.
8. 개별 container가 CPU/메모리/시간 제한을 초과하면 해당 container만 종료하고 DB에는 최종 결과만 짧게 기록합니다.

## 현재 적용 예

### 상점 구매
구매 idempotency 상태와 잔액·Inventory를 함께 변경하므로 사용자 row를 짧게
잠급니다. 잠금 후 서버 가격과 `soft_balance >= price`를 확인하고 동일
transaction에서 차감과 수량 증가를 수행합니다.

```sql
SELECT id, soft_balance FROM users WHERE id = :user_id FOR UPDATE;
```

`inventories.last_purchase_request_id`의 UNIQUE 제약과 사용자 row 잠금으로 같은
요청 ID의 동시 재전송을 한 번만 적용합니다. 외부 I/O 없이 짧은 DB transaction
안에서 끝냅니다.

### 출석/중복 보상
`UNIQUE(user_id, check_in_date)` 같은 DB 제약을 우선합니다.

### 하우징 가구 배치
같은 가구의 동시 배치 요청이 Inventory 수량을 함께 통과하지 않도록 해당
`(user_id, item_id)` Inventory 행을 짧게 잠급니다. 잠금 후 현재 배치 개수를
계산하고 `placed_count < quantity`인 경우에만 `placed_objects`를 추가합니다.

```sql
SELECT * FROM inventories
WHERE user_id = :user_id AND item_id = :item_id AND quantity > 0
FOR UPDATE;
```

위치 변경과 회수에는 외부 I/O가 없으며 대상 소유권을 같은 transaction에서
확인합니다.

### 방 참가
방 상태, 정원, 참가자 추가를 한 트랜잭션에서 직렬화해야 하므로 Room row에 대한 짧은 `FOR UPDATE`는 허용합니다.

## Docker 채점 트랜잭션 경계

권장 흐름:

```text
POST /attempts
  -> TaskAttempt(PENDING) INSERT
  -> COMMIT
  -> HTTP 202

Background task
  -> 실행 슬롯 확보
  -> Docker 실행/채점/정리
  -> 짧은 DB transaction으로 결과 UPDATE
  -> COMMIT
```

금지 흐름:

```text
BEGIN
  -> DB row lock
  -> Docker 실행 수 초
  -> 결과 기록
COMMIT
```

Docker 실행 중 DB transaction이 살아 있지 않도록 설계합니다.
