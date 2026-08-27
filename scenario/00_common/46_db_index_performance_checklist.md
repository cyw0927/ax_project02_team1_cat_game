# DB 인덱스·조회 성능 체크리스트

이 문서는 PostgreSQL에서 자주 조회하는 컬럼에 **어디까지 인덱스를 둘지**, 그리고 초보 팀이 불필요하게 인덱스를 남발하지 않도록 기준을 정리한다.

핵심은 다음이다.

```text
인덱스가 많다고 무조건 빠른 것은 아니다.

자주 조회/정렬/조인하는 컬럼
→ 인덱스 후보

거의 조회하지 않는 컬럼
→ 굳이 인덱스 만들지 않음
```

---

## 1. PK와 UNIQUE

Primary Key에는 기본적으로 인덱스가 생긴다.

UNIQUE 제약도 PostgreSQL에서 유일성 검사를 위한 unique index를 만든다.

따라서 이미 다음과 같은 UNIQUE를 둔다면 같은 컬럼 조합의 중복 인덱스를 또 만들 필요가 없다.

예:

```text
ATTENDANCES(user_id, check_in_date)
INVENTORIES(user_id, item_id)
ROOM_PARTICIPANTS(room_id, user_id)
RANKING_PARTICIPANTS(group_id, user_id)
```

---

## 2. Foreign Key 주의

PostgreSQL은 FK를 만들었다고 해서 **참조하는 쪽 FK 컬럼에 항상 자동 인덱스를 만들어 주는 것은 아니다.**

따라서 실제 조회 패턴을 보고 FK 컬럼 인덱스를 검토해야 한다.

예:

```text
TASK_ATTEMPTS.user_id
TASK_ATTEMPTS.task_id
PLACED_OBJECTS.user_id
USER_CATS.user_id
CAT_MEMORIES.user_cat_id
```

---

## 3. USERS

`USERS.id`는 PK이므로 기본 조회는 문제없다.

인증에서 username으로 로그인한다면:

```text
WHERE username = ?
```

조회가 자주 발생하므로 `username UNIQUE`를 채택할 경우 unique index가 같이 생긴다.

아직 username UNIQUE 정책은 인증 설계와 함께 확정한다.

---

## 4. ATTENDANCES

주요 조회:

```text
오늘 사용자 출석 존재 여부
사용자 최근 출석 기록
사용자 streak 계산
```

이미 중요한 제약:

```text
UNIQUE(user_id, check_in_date)
```

이 조합은 오늘 출석 확인에 그대로 활용 가능하다.

최근 기록 조회가 많다면:

```text
(user_id, check_in_date DESC)
```

형태의 별도 인덱스 필요성을 실제 쿼리로 확인할 수 있지만 MVP에서 먼저 남발하지 않는다.

---

## 5. TASKS

주요 조회:

```text
is_active = true
concept_id = ?
difficulty = ?
```

문제 수가 적은 MVP에서는 full scan이어도 문제가 없을 수 있다.

문제은행이 커질 때 다음 조합을 검토할 수 있다.

```text
concept_id
is_active
(concept_id, is_active)
```

실제 filter 조합을 보고 결정한다.

---

## 6. TASK_ATTEMPTS

주요 조회:

```text
사용자의 최근 시도
특정 task의 과거 PASSED 여부
특정 attempt polling
오래된 PENDING/RUNNING 찾기
```

PK polling은 `id`로 해결된다.

추가 후보:

```text
(user_id, attempted_at)
(user_id, task_id)
(status, attempted_at)
```

특히 `status + attempted_at`은 stale PENDING 정리를 실제로 자주 수행할 때 도움이 될 수 있다.

다만 행 수가 적을 때는 먼저 필요성을 측정한다.

---

## 7. ROOMS

방 목록에서 흔한 조건:

```text
status = WAITING
```

방 수가 많아지면 `status` 인덱스를 검토할 수 있다.

하지만 게임 방 수가 적은 MVP에서 인덱스 하나 때문에 설계를 복잡하게 만들 필요는 없다.

---

## 8. ROOM_PARTICIPANTS

이미:

```text
UNIQUE(room_id, user_id)
```

가 있으면 방 안의 특정 사용자 존재 확인에 유리하다.

자주 하는 조회:

```text
WHERE room_id = ?
```

복합 인덱스의 첫 컬럼이 `room_id`라면 방별 참가자 조회에도 활용될 수 있다.

---

## 9. ROOM_TASKS

제약 후보:

```text
UNIQUE(room_id, task_id)
UNIQUE(room_id, task_order)
```

특히 `(room_id, task_order)`는 배틀 문제 순서 조회에 그대로 유용하다.

---

## 10. RANKING_PARTICIPANTS

랭킹 화면은 보통:

```text
WHERE group_id = ?
ORDER BY current_rank_score DESC
```

형태가 될 수 있다.

데이터가 커지면:

```text
(group_id, current_rank_score DESC)
```

인덱스 후보가 된다.

소규모 그룹이라면 당장 필요하지 않을 수 있다.

---

## 11. RANK_CHALLENGES

주요 조회:

```text
사용자의 현재 IN_PROGRESS challenge
만료된 IN_PROGRESS challenge
```

후보:

```text
(user_id, status)
(status, expires_at)
```

활성 challenge 중복을 어떤 DB 제약으로 막을지 확정되면 인덱스 구조도 함께 검토한다.

---

## 12. INVENTORIES

이미:

```text
UNIQUE(user_id, item_id)
```

가 있으면 사용자 특정 item 소유 여부 및 upsert에 적합하다.

사용자 전체 inventory 조회도 복합 index의 첫 컬럼이 user_id이므로 활용 가능하다.

---

## 13. PLACED_OBJECTS

하우스 화면은:

```text
WHERE user_id = ?
```

로 배치 오브젝트를 한꺼번에 읽는다.

따라서 `user_id`는 인덱스 후보 가치가 높다.

현재 실제 migration에 해당 인덱스가 있는지는 구현 단계에서 확인해야 한다.

---

## 14. USER_CATS

주요 조회:

```text
WHERE user_id = ?
```

사용자 보유 고양이 목록이 자주 열리므로 `user_id` 인덱스를 검토한다.

중복 고양이 정책이 확정되면 `(user_id, cat_id)` UNIQUE 여부도 달라질 수 있으므로 미리 확정하지 않는다.

---

## 15. CAT_MEMORIES

고양이 대화 전:

```text
WHERE user_cat_id = ?
```

조회가 반복될 수 있다.

현재 한 USER_CAT당 메모리 row를 몇 개 둘지 확정되지 않았다.

한 row만 유지한다면 `user_cat_id UNIQUE`까지 검토할 수 있지만, 여러 메모리 row를 쌓을 계획이면 일반 index가 맞다.

---

## 16. ORDER BY와 Pagination

목록 API에서:

```text
ORDER BY created_at DESC
LIMIT ... OFFSET ...
```

같은 패턴이 많아지면 정렬 컬럼 인덱스가 중요할 수 있다.

하지만 현재 ERD 일부 테이블에는 created_at 자체가 없다.

Pagination 요구를 위해 무작정 timestamp 컬럼을 추가하지 말고 실제 화면 요구와 함께 설계한다.

---

## 17. 인덱스가 너무 많으면 생기는 문제

INSERT/UPDATE 시 인덱스도 같이 갱신해야 한다.

따라서:

```text
읽기는 조금 빨라질 수 있음
쓰기 비용/저장공간은 증가
migration도 복잡해짐
```

이라는 대가가 있다.

특히 작은 테이블에는 인덱스가 거의 의미 없을 수 있다.

---

## 18. 성능 문제 확인 순서

느리다고 느껴지면 먼저:

1. 어떤 API가 느린지
2. 실제 SQL이 무엇인지
3. 반환 row 수가 몇 개인지
4. N+1 query가 있는지
5. 불필요하게 전체 테이블을 읽는지
6. 그 다음 `EXPLAIN`/`EXPLAIN ANALYZE` 검토
7. 필요한 인덱스 추가

순서로 간다.

처음부터 예상만으로 모든 컬럼에 index를 붙이지 않는다.

---

## 19. SQLAlchemy 관계와 N+1

ORM을 사용할 때 목록을 가져온 뒤 row마다 별도 SELECT를 반복하면 N+1 문제가 생길 수 있다.

예:

```text
room 20개 조회 = 1 query
각 room 참가자 조회 = 20 query
총 21 query
```

필요하면 join/eager loading 또는 별도 batch query를 검토한다.

MVP에서도 이상하게 query가 많이 나가면 먼저 이 부분을 확인한다.

---

## 20. Migration

인덱스 추가/삭제는 Alembic migration으로 관리한다.

```text
개발자 로컬 DB에만 수동 CREATE INDEX
```

해놓고 migration을 안 남기면 팀원 DB와 달라진다.

---

## 21. 초기 우선 확인 후보

실제 구현 전에 무조건 생성한다는 뜻이 아니라 **쿼리 패턴상 먼저 확인할 후보**다.

```text
ATTENDANCES(user_id, check_in_date) UNIQUE
ROOM_PARTICIPANTS(room_id, user_id) UNIQUE
ROOM_TASKS(room_id, task_order) UNIQUE
RANKING_PARTICIPANTS(group_id, user_id) UNIQUE
INVENTORIES(user_id, item_id) UNIQUE
PLACED_OBJECTS.user_id
USER_CATS.user_id
TASK_ATTEMPTS.user_id / status+attempted_at 사용 빈도
```

---

# 결론

인덱스는 ERD를 예쁘게 만드는 장식이 아니라 **실제 query를 빠르게 만드는 도구**다.

```text
먼저 query 패턴 확인
→ 이미 PK/UNIQUE index가 있는지 확인
→ 느린 구간 측정
→ 필요한 index만 Alembic으로 추가
```

이 순서를 따른다.