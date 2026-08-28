# 목록 조회 Pagination·Filter·Sort 정책

이 문서는 목록 API가 데이터가 늘어났을 때 한 번에 모든 row를 반환하지 않도록 공통 조회 규칙을 정리한다.

## 1. 대상 API

초기에는 데이터가 적어 전체 반환도 가능하지만 다음은 목록이 커질 수 있다.

```text
GET /tasks
GET /users/{user_id}/attempts
GET /rooms
GET /ranking-groups
GET /ranking-groups/{group_id}/participants
GET /items
GET /users/{user_id}/inventory
GET /cats
GET /users/{user_id}/cats
GET /users/{user_id}/attendance
```

## 2. MVP 기본 선택

작은 데이터셋은 단순 전체 조회로 시작해도 된다. 다만 `TASK_ATTEMPTS`, 방 목록, 랭킹처럼 계속 쌓이는 데이터는 Pagination을 먼저 검토한다.

추천 초안:

```http
GET /users/me/attempts?page=1&size=20
```

Response 예:

```json
{
  "items": [],
  "page": 1,
  "size": 20,
  "total": 57
}
```

정확한 포맷은 팀 API 계약에 맞춘다.

## 3. size 제한

클라이언트가:

```text
size=1000000
```

을 보내도 그대로 처리하지 않는다.

서버가 최소/최대 범위를 검증한다.

예:

```text
1 <= size <= 서버 설정 최대값
```

정확한 최대값은 설정으로 둘 수 있다.

## 4. Filter

Filter는 화면에서 실제 필요한 조건만 지원한다.

### TASKS

후보:

```text
concept_id
difficulty
type
is_active(관리자용)
```

일반 사용자에게는 기본적으로 활성 task만 노출한다.

### ROOMS

후보:

```text
status
내가 참가한 방
입장 가능한 방
```

### ITEMS

후보:

```text
category
```

### ATTEMPTS

후보:

```text
task_id
status
concept_id
```

불필요한 필터를 처음부터 모두 만들지 않는다.

## 5. Sort

정렬 기준은 서버에서 허용 목록을 둔다.

예:

```text
attempted_at desc
current_rank_score desc
price asc/desc
```

클라이언트가 SQL 컬럼명이나 임의 문자열을 그대로 전달해 동적 SQL에 넣지 않는다.

## 6. 안정적인 정렬

같은 값이 여러 행에 있을 수 있으므로 필요하면 보조 정렬키를 둔다.

예:

```text
ORDER BY attempted_at DESC, id DESC
```

이렇게 해야 페이지를 넘길 때 순서가 들쭉날쭉해지는 문제를 줄일 수 있다.

## 7. Offset vs Cursor

MVP는 이해하기 쉬운 page/size(offset 방식)로 충분하다.

데이터가 매우 커지거나 실시간으로 계속 추가되는 목록은 cursor pagination을 검토할 수 있지만 현재 단계에서 과도하게 복잡하게 만들 필요는 없다.

## 8. 프론트 UX

목록 API에서는 다음 상태를 구분한다.

```text
로딩 중
결과 있음
결과 0건
추가 페이지 있음
API 실패
```

0건은 오류가 아니다.

예:

```json
{"items": [], "page": 1, "size": 20, "total": 0}
```

처럼 정상 Response가 자연스럽다.

## 9. 테스트

- 첫 페이지
- 마지막 페이지
- 결과 0건
- size 최소/최대 경계
- 잘못된 filter 값
- 허용하지 않은 sort
- 같은 정렬값이 여러 개일 때 순서 안정성

## 핵심

Pagination/Filter/Sort는 모든 API에 억지로 넣는 기능이 아니라 **실제로 데이터가 쌓이고 화면에서 필요한 목록부터 적용**한다.