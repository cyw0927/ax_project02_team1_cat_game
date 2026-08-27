# 보상·재화 변경 지점 정리

이 문서는 프로젝트 전체에서 **언제 USERS의 재화가 증가하거나 감소하는지**를 모아보기 위한 문서다.

재화 규칙의 정확한 숫자는 아직 기획에서 계속 조정될 수 있으므로 여기서는 금액을 확정하지 않고, **어떤 이벤트가 재화를 건드리는지와 어떤 방어가 필요한지**만 정리한다.

최신 제품 흐름에서는 다음 세 기능이 재화의 주요 생산 경로가 된다.

```text
학습 정답
배틀 결과
승급전 성공
     ↓
   재화 획득
     ↓
상점 / 가챠에서 소비
```

출석 역시 별도의 보상 경로다.

---

# 1. 학습 정답 보상

## 발생 시점

Docker 채점 결과가 `PASSED`로 확정된 뒤.

## 중요한 조건

같은 문제를 반복 제출해서 재화를 무한히 얻을 수 없어야 한다.

추천 흐름:

```text
attempt PASSED
→ 이 사용자/이 문제의 보상 자격 확인
→ 보상 가능하면 USERS 재화 증가
→ attempt 결과와 함께 commit
```

## 위험

같은 문제를 거의 동시에 두 번 제출해서 둘 다 정답이 되는 경우.

두 worker가 동시에:

```text
이전 정답 없음
```

을 확인하면 중복 보상이 생길 수 있다.

따라서 최초 보상 확정 구간은 동시성 방어가 필요하다.

현재 ERD를 유지한다면 사용자 row를 짧게 잠그고 과거 PASSED를 재확인하는 방법을 검토할 수 있다.

정확한 보상 횟수/일일 제한은 기획 규칙 확정이 필요하다.

---

# 2. 힌트 사용 보상

`TASK_ATTEMPTS.used_hint`가 있기 때문에 힌트 사용 여부에 따라 보상을 다르게 줄 수 있다.

후보:

```text
A. 힌트 사용해도 동일 보상
B. 힌트 사용 시 일부 보상
C. 힌트 사용 시 재화 없음, 학습 완료만 인정
```

현재는 확정하지 않는다.

백엔드는 `used_hint`를 attempt 생성 시 기록해 두고 최종 보상 단계에서 참고할 수 있다.

---

# 3. 출석 보상

## 발생 시점

당일 `ATTENDANCES` INSERT가 성공한 경우.

## transaction

```text
ATTENDANCES INSERT
+ USERS 재화 증가
→ 같은 transaction
```

보상 지급 실패 시 출석 row만 남아버리면 사용자가 다시 보상을 받을 수 없게 된다.

따라서 중간 실패 시 전체 rollback이 필요하다.

## 중복 방어

```text
UNIQUE(user_id, check_in_date)
```

DB가 하루 한 번만 성공하도록 보장한다.

---

# 4. 배틀 결과 보상

최신 흐름도에서는:

```text
배틀
→ 문제 풀이
→ 점수 경쟁
→ 배틀 결과 보상
→ 재화 획득
```

으로 연결된다.

## 아직 결정해야 할 것

```text
승리자만 보상?
참가자 모두 보상?
팀전은 팀원 전원 동일 보상?
순위별 차등?
하루 횟수 제한?
중도 이탈자는 보상 제외?
```

이 규칙이 정해지기 전에는 점수 기능과 보상 기능을 강하게 결합하지 않는다.

## 중복 지급 위험

`finish` API를 두 번 호출하거나 서버가 재처리하면 같은 방 보상이 반복 지급될 수 있다.

현재 ERD에는 `battle_reward_claimed` 같은 컬럼/보상 이력 테이블이 없다.

따라서 배틀 보상을 실제 구현하기 전에는 **한 방의 결과 보상을 한 번만 지급했다는 사실을 어디에 기록할지** 반드시 설계해야 한다.

이 부분은 현재 19테이블 ERD에서 추가 검토가 필요한 지점이다.

---

# 5. 승급전 성공 보상

최신 흐름도에서는:

```text
승급전 도전
→ 문제 풀이
→ 성공
→ 승급 성공 보상
→ 재화 획득
```

이다.

## 조건

```text
RANK_CHALLENGES.status가 SUCCESS로 확정
```

된 뒤 한 번만 지급해야 한다.

## 중복 지급 위험

SUCCESS 상태인 challenge에 완료 로직이 다시 실행되면 보상이 반복될 수 있다.

따라서:

```text
IN_PROGRESS → SUCCESS
```

로 처음 전환되는 transaction 안에서 보상을 같이 처리하는 방법을 검토한다.

이미 SUCCESS인 challenge의 완료 API는 보상을 다시 지급하지 않는다.

---

# 6. 상점 구매 — 재화 감소

## 발생 시점

사용자가 아이템 구매 확정.

## 원칙

Python 메모리에서:

```text
잔액 읽기
→ 빼기
→ 다시 저장
```

하지 않는다.

DB에 직접:

```sql
UPDATE users
SET balance = balance - :price
WHERE id = :user_id
  AND balance >= :price;
```

를 수행한다.

## transaction

```text
ITEM 가격 확인
→ USERS Atomic Update
→ INVENTORIES INSERT/upsert
→ COMMIT
```

Inventory 저장 실패 시 잔액 감소도 rollback되어야 한다.

---

# 7. 가챠 — 재화 감소

가챠 역시 상점처럼 재화를 먼저 소비한다.

추천 transaction:

```text
가챠 가격/규칙 확인
→ USERS 재화 Atomic Update
→ CATS 후보 추첨
→ USER_CATS 결과 저장
→ 중복/마일리지 정책 처리
→ COMMIT
```

중간에 하나라도 실패하면:

```text
ROLLBACK
```

한다.

즉:

```text
재화는 줄었는데 고양이는 없음
```

이라는 상태가 생기면 안 된다.

---

# 8. 마일리지 변경

ERD의 `USERS.mileage`는 향후 가챠 중복 처리 등에 사용할 수 있다.

하지만 현재 정확한 용도는 최종 확정이 필요하다.

후보:

```text
중복 고양이 → mileage 증가
mileage 일정량 → 원하는 고양이/아이템 교환
```

마일리지 역시 사용자 자산이므로 증가/차감은 transaction과 동시성을 고려한다.

---

# 9. 현재 balance 하나로 충분한가

기획에서 재화 종류가 늘어나면 현재:

```text
USERS.balance
USERS.mileage
```

만으로 부족할 수 있다.

예를 들어 싼 재화/비싼 재화/마일리지를 모두 별도로 유지한다면 USERS 컬럼 확장 또는 별도 경제 구조 검토가 필요하다.

다만 이 문서에서는 어떤 재화 체계를 채택할지 확정하지 않는다.

재화 기획 확정 후 ERD와 API를 맞춘다.

---

# 10. 재화 변경 API 공통 질문

재화를 건드리는 모든 로직에서 아래를 확인한다.

```text
1. 이 보상/차감은 몇 번까지 가능한가?
2. 같은 요청을 동시에 두 번 보내면 어떻게 되는가?
3. 중간 DB 오류가 나면 전부 rollback되는가?
4. 프론트가 보내는 금액을 믿고 있지는 않은가?
5. 가격/보상량은 서버 기준인가?
6. 성공 Response에 최종 잔액을 보내는가?
7. 같은 이벤트를 다시 처리해도 중복 보상이 안 생기는가?
```

특히 가격은 프론트에서:

```json
{
  "item_id": 5,
  "price": 200
}
```

처럼 받아서 믿지 않는다.

프론트는 `item_id`만 보내고 서버가 `ITEMS.price`를 조회하는 것이 기본이다.

---

# 11. 재화 변경 Before / After 예

## 상점

Before:

```text
USERS.balance = 1000
INVENTORY(item=5) = 1
```

가격이 200인 item을 정상 구매.

After:

```text
USERS.balance = 800
INVENTORY(item=5) = 2
```

## 출석

Before:

```text
오늘 ATTENDANCE 없음
balance = X
```

After:

```text
오늘 ATTENDANCE 1행
balance = X + reward
```

두 번째 호출:

```text
UNIQUE 충돌
balance 변화 없음
```

## 가챠

Before:

```text
balance = X
USER_CATS = N개
```

After:

```text
balance = X - cost
USER_CATS = N+1 또는 중복 정책 결과
```

가챠 저장 실패:

```text
balance = X
USER_CATS = N개
```

원상복구되어야 한다.

---

# 결론

게임 경제는 `얼마를 주느냐`만의 문제가 아니다.

백엔드 관점에서는 더 먼저:

```text
언제 지급/차감되는가
누가 받을 수 있는가
몇 번 가능한가
동시에 요청하면 어떻게 되는가
실패하면 rollback되는가
중복 지급을 어떻게 막는가
```

를 정해야 한다.

정확한 재화 이름과 숫자가 바뀌더라도 이 구조적 원칙은 그대로 유지할 수 있다.