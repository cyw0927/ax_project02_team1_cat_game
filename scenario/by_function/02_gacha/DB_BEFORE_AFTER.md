# B. 가챠·고양이 DB Before / After

이 문서는 가챠가 구현될 때 **재화 차감과 고양이 지급이 DB에서 어떻게 같이 움직여야 하는지** 정리한다.

현재 `main`에는 가챠 쓰기 API가 없으므로 대부분 향후 구현 기준이다.

가격·확률·중복·천장 숫자는 기획 확정 전 임의로 넣지 않는다.

---

## B-DB01. 고양이 목록 조회 — 현재

### Before

`CATS`

```text
C1
C2
C3
```

### API

```http
GET /cats
```

### After

DB 변화 없음.

---

## B-DB02. 내 고양이 조회 — 현재

### Before

```text
USER_CATS
UC1 user=U1 cat=C1
UC2 user=U1 cat=C3
UC3 user=U2 cat=C2
```

### API

```http
GET /users/U1/cats
```

### After

DB 변화 없음.

U1의 UC1, UC2만 조회되어야 한다.

---

## B-DB03. 정상 1회 가챠 — 향후

### Before 예시

```text
USERS.U1.balance = 충분한 잔액
USER_CATS = 기존 보유 상태
```

### 처리

```text
BEGIN
→ 서버가 비용 결정
→ USERS 재화 조건부 Atomic 차감
→ 서버가 결과 추첨
→ USER_CATS INSERT 또는 확정 중복 보상 처리
→ mileage/티켓 등이 있다면 같이 반영
→ COMMIT
```

### After

최소:

```text
USERS.U1 재화 = Before - 서버 비용
USER_CATS = 결과에 따라 1개 증가 또는 확정된 중복 처리
```

Response는 DB commit 후 최종 잔액과 결과를 반환한다.

---

## B-DB04. 잔액 부족

### Before

```text
USERS.U1 재화 < 1회 비용
```

### 처리

조건부 Atomic UPDATE가 성공하지 않음.

### After

```text
USERS 재화 변화 없음
USER_CATS 변화 없음
mileage/티켓 변화 없음
```

---

## B-DB05. 결과 저장 실패 rollback

### Before

사용자는 충분한 재화를 가지고 있다.

### transaction 중

```text
재화 차감 성공
→ USER_CATS INSERT에서 DB 오류
```

### 올바른 처리

```text
ROLLBACK
```

### After

```text
재화 = Before와 동일
USER_CATS = Before와 동일
mileage/티켓 = Before와 동일
```

사용자가 돈만 잃는 반쪽 성공을 허용하지 않는다.

---

## B-DB06. 동시에 여러 가챠 요청

### Before

사용자 잔액이 1회분만 남아 있다고 가정.

### 동시에

```text
Request A
Request B
Request C
```

### 목표

Atomic 차감 때문에 허용 가능한 요청만 성공한다.

### After

```text
잔액 음수 금지
성공한 pull 수 = 실제 지급 결과 수
```

---

## B-DB07. 중복 고양이 — 정책 미정

현재 DB에는:

```text
USER_CATS(user_id, cat_id) UNIQUE 없음
```

따라서 같은 cat master를 여러 row로 소유할 수 있다.

### 정책 A: 중복도 별도 소유

Before:

```text
UC1 user=U1 cat=C7
```

당첨 C7.

After:

```text
UC1 user=U1 cat=C7
UC2 user=U1 cat=C7
```

### 정책 B: 중복을 mileage로 전환

After 예시 개념:

```text
USER_CATS 변화 없음
USERS.mileage 증가
```

어느 쪽도 현재 확정하지 않는다.

---

## B-DB08. 다회 가챠 — 정책 미정

다회 pull을 채택한다면:

```text
BEGIN
→ 총 비용 차감
→ N개 결과 생성
→ 모든 지급 row 저장
→ 부가 보상 저장
→ COMMIT
```

중간 5번째 결과 저장 실패 시 처리 정책은 가능하면 전체 rollback으로 단순화한다.

### After 목표

```text
차감된 pull 수와 실제 결과 수가 불일치하지 않음
```

---

## B-DB09. 네트워크 중복 요청

같은 클라이언트 요청이 재전송되는 경우를 한 번만 인정하기로 한다면 idempotency 저장 구조가 필요할 수 있다.

### 목표 After

같은 idempotency key가 두 번 오면:

```text
재화 차감 1회
가챠 결과 지급 1회
```

정상적으로 사용자가 두 번 누른 별도 요청과는 구분해야 한다.

현재 저장 구조는 미정이다.

---

## B-DB10. 천장 — 정책/스키마 미정

천장을 도입한다면 사용자별 누적 상태가 영속 저장되어야 한다.

### 필요한 Before/After 개념

```text
Before: pity_count = N
일반 결과: pity_count = N+1
천장 발동: 보장 결과 지급 + pity_count reset
```

현재 19테이블 ERD에는 전용 pity 상태가 없다.

천장 도입 확정 전 migration을 만들지 않는다.

---

## B-DB11. 고양이 대화

### Before

```text
USER_CATS.UC1 owner=U1
CATS.C1 persona=...
CAT_MEMORIES = 기존 summary
```

### 처리

```text
ownership 확인
→ persona/memory 조회
→ DB transaction 종료
→ LLM 호출
→ 필요한 경우 새 짧은 transaction으로 memory 갱신
```

### 중요한 점

외부 LLM 응답을 기다리는 동안 USER_CATS 소유 row를 lock한 채 두지 않는다.

---

## B-DB12. LLM 실패

### Before

고양이 소유 정보 정상.

### 외부 호출 실패

### After

```text
USER_CATS 변화 없음
CATS master 변화 없음
기존 CAT_MEMORIES를 손상시키지 않음
```

memory update가 실패해도 고양이 소유 자체가 rollback되거나 삭제되면 안 된다.

---

# 한눈에 보는 핵심

```text
가챠 성공
재화 차감 + 결과 지급 = 같은 transaction

가챠 실패
재화와 결과 모두 Before로 rollback

동시 요청
Atomic 차감으로 음수 잔액 방지

중복/천장
정책과 저장 구조 확정 후 구현
```

가챠 DB에서 가장 중요한 것은 확률 연출보다 **사용자가 돈만 잃거나 결과를 중복으로 받는 상태를 막는 것**이다.
