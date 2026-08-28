# DB 제약조건과 Migration 체크리스트

ERD 선만 맞는다고 DB 설계가 끝난 것은 아니다. 실제 동시 요청과 중복 데이터를 막기 위해 UNIQUE/FK/NULL/기본값을 같이 확인해야 한다.

## 1. 반드시 검토할 UNIQUE

현재 구조에서 우선 확인할 후보:

```text
ATTENDANCES(user_id, check_in_date)
INVENTORIES(user_id, item_id)
ROOM_PARTICIPANTS(room_id, user_id)
ROOM_TASKS(room_id, task_id)
ROOM_TASKS(room_id, task_order)
RANKING_PARTICIPANTS(group_id, user_id)
RANK_CHALLENGE_TASKS(challenge_id, task_id)
RANK_CHALLENGE_TASKS(challenge_id, task_order)
```

인증을 아이디 기반으로 확정하면:

```text
USERS(username)
```

UNIQUE도 검토한다.

## 2. FK 삭제 정책

FK가 있다고 끝이 아니다. 부모를 삭제했을 때 자식 데이터를 어떻게 할지 정해야 한다.

예:
- 사용자를 삭제하면 학습 로그를 같이 삭제할지
- 문제를 삭제하지 않고 `is_active=false`로 유지할지
- 방 삭제 시 참가자/문제 배정을 같이 삭제할지
- 고양이 마스터 삭제 시 USER_CATS를 어떻게 할지

로그 보존이 중요한 `TASKS`, `TASK_ATTEMPTS`는 무작정 cascade delete하지 않는 방향을 우선 검토한다.

## 3. NULL 허용 여부

의미가 있는 NULL만 허용한다.

예:
- `ROOM_PARTICIPANTS.team_name`: 개인전이면 NULL 가능
- `RANK_CHALLENGE_TASKS.saved_code`: 아직 입력하지 않았다면 NULL 가능
- `USERS.wallpaper_item_id`, `floor_item_id`: 기본 배경을 별도 item으로 만들지 않는다면 NULL 가능성 검토

반대로 반드시 값이 있어야 하는 status, price, quantity 등을 nullable로 두면 데이터가 꼬일 수 있다.

## 4. CHECK 제약 후보

PostgreSQL CHECK로 막을 가치가 있는 값도 검토한다.

예:

```text
balance >= 0
mileage >= 0
quantity >= 0
max_participants > 0
current_score >= 0 (감점 정책이 없을 경우)
```

단, 비즈니스 정책이 아직 미정이면 먼저 확정하고 제약을 건다.

## 5. status 문자열

현재 문자열 status가 많다.

```text
ROOMS.status
TASK_ATTEMPTS.status
RANK_CHALLENGES.status
```

MVP에서는 String으로 유지할 수 있지만 허용값을 코드에서 일관되게 관리해야 한다. DB Enum/Check를 쓸지는 migration 복잡도와 팀 숙련도를 보고 결정한다.

## 6. JSONB 검증

`PLACED_OBJECTS.position_data`가 JSONB라고 해서 아무 JSON이나 저장해도 된다는 뜻은 아니다.

API에서 최소한 다음 구조를 검증하는 방향을 검토한다.

```json
{
  "x": 2,
  "y": 4,
  "rotation": 90
}
```

필드 이름과 타입을 Pydantic에서 검사하면 DB 안에 제각각 다른 JSON이 쌓이는 것을 줄일 수 있다.

## 7. Migration 작업 순서

```text
ERD/비즈니스 규칙 확정
→ SQLAlchemy model 수정
→ Alembic revision 작성
→ upgrade 테스트
→ 실제 테이블 확인
→ downgrade 필요성 확인
→ PR
```

## 8. 여러 명이 migration을 동시에 만들지 않기

두 branch가 같은 base revision에서 각자 migration을 만들면 merge 후 Alembic head가 갈라질 수 있다. 교육 프로젝트에서는 가능한 한 DB 변경 담당 순서를 정하고 한 번에 하나씩 merge하는 것이 단순하다.

## 9. 기존 데이터가 있을 때

새 NOT NULL 컬럼을 추가하면 기존 row에 값을 어떻게 채울지 필요하다.

예를 들어 `TASKS.title`을 추가한다면:

1. nullable로 먼저 추가
2. 기존 데이터 backfill
3. 필요하면 NOT NULL로 변경

같은 순서를 검토할 수 있다.

## 10. migration 완료 확인

- 새 DB에서 처음부터 upgrade 가능한가
- 기존 DB에서 최신 revision까지 upgrade 가능한가
- 모델과 실제 DB 컬럼이 같은가
- UNIQUE/FK가 실제 DB에 생성됐는가
- DBeaver에서 constraint를 확인했는가

코드에 `UniqueConstraint`를 적었다는 사실만으로 끝내지 않고 실제 DB 반영을 확인한다.