# D. 랭킹·승급전 API 명세 초안

이 문서는 `04_rank_challenge` 시나리오를 실제 API 계약으로 옮기기 위한 초안이다.

현재 `main`에는 랭킹 조회, 승급전 생성, 문제 목록 조회, 코드 임시 저장까지 구현돼 있다. 실제 문제 제출·채점·SUCCESS/FAILED/TIMEOUT·점수/보상 반영은 아직 없다.

문제 수, 제한시간, 합격 기준, 점수 증감, 보상량은 기획 확정 전 임의로 정하지 않는다.

---

## 1. 랭킹 그룹 목록

### Endpoint

```http
GET /ranking-groups
```

### 현재 구현

구현됨.

### Response

```json
[
  {
    "id": "group-uuid",
    "name": "...",
    "owner_user_id": "user-uuid"
  }
]
```

### DB

- `RANKING_GROUPS` Read

---

## 2. 그룹 랭킹 조회

### Endpoint

```http
GET /ranking-groups/{group_id}/participants
```

### 현재 구현

구현됨.

### Response

```json
[
  {
    "user_id": "user-uuid",
    "username": "...",
    "current_rank_score": 0
  }
]
```

현재 score 내림차순으로 조회한다.

### 상태코드

- 그룹 있음: `200`
- 그룹 없음: `404`

---

## 3. 사용자 참여 랭킹 그룹 조회

### Endpoint

```http
GET /users/{user_id}/ranking-groups
```

### 현재 구현

구현됨.

JWT 이후 `/me/ranking-groups` 후보.

---

## 4. 사용자 승급전 이력

### Endpoint

```http
GET /users/{user_id}/rank-challenges
```

### 현재 구현

구현됨.

### Response 필드

```text
challenge_id
group_id
group_name
status
started_at
expires_at
```

JWT 이후 `/me/rank-challenges` 후보.

---

## 5. 승급전 시작

### Endpoint

```http
POST /ranking-groups/{group_id}/rank-challenges
```

### 현재 Request

```json
{
  "user_id": "user-uuid",
  "task_ids": ["task-uuid-1", "task-uuid-2"],
  "expires_at": "2026-08-27T12:00:00Z"
}
```

### 현재 처리

```text
server now 계산
→ expires_at 미래인지 확인
→ ranking participant 확인
→ 동일 group/user의 active challenge 확인
→ task_ids 중복 확인
→ 모두 active TASK인지 확인
→ RANK_CHALLENGES INSERT
→ RANK_CHALLENGE_TASKS 순서대로 INSERT
→ COMMIT
```

challenge와 tasks는 같은 transaction에 저장된다.

### 상태코드

- 성공: `201 Created`
- expires_at 잘못됨/중복 task: `400`
- ranking participant/task 없음: `404`
- active challenge 존재: `409`

---

## 6. 승급전 시작 API의 향후 변경 후보

현재는 프론트가:

```text
task_ids
expires_at
```

을 정한다.

기획에서:

```text
한 번에 몇 문제
어떤 난이도
제한시간 몇 분
```

이 서버 규칙으로 확정되면 Request를 다음처럼 줄이는 편이 더 안전하다.

```json
{}
```

또는 사용자 선택이 필요한 최소 옵션만 받는다.

서버가:

```text
문제 선택
started_at
expires_at
```

을 결정한다.

이 변경은 프론트 계약 영향이 크므로 한 번에 맞춘다.

---

## 7. 승급전 문제 목록

### Endpoint

```http
GET /rank-challenges/{challenge_id}/tasks
```

### 현재 구현

구현됨.

### 현재 Response

```json
[
  {
    "task_order": 1,
    "task_id": "task-uuid",
    "concept_id": 1,
    "type": "function",
    "difficulty": "...",
    "template_code": "...",
    "is_passed": false,
    "has_saved_code": true
  }
]
```

### 주의

현재 실제 `saved_code`는 반환하지 않고 `has_saved_code`만 반환한다.

재접속 후 코드를 복원해야 한다면 별도 상세 API 또는 이 Response에 `saved_code`를 포함할지 결정해야 한다.

`test_cases`는 노출하지 않는다.

---

## 8. 코드 임시 저장

### Endpoint

```http
PUT /rank-challenges/{challenge_id}/tasks/{task_id}/code
```

### 현재 Request

```json
{
  "user_id": "user-uuid",
  "saved_code": "..."
}
```

### 현재 처리

```text
challenge + user 확인
→ status == IN_PROGRESS
→ expires_at > server now
→ challenge task 확인
→ saved_code UPDATE
→ COMMIT
```

### 현재 구현

구현됨.

JWT 도입 후 user_id는 토큰 기준으로 바꾼다.

---

## 9. 코드 복원

### 현재 상태

**PARTIAL**.

현재 문제 목록은 `has_saved_code`만 반환하므로 사용자가 실제 코드를 이어서 작성하려면 저장된 코드 반환 방식이 필요하다.

후보 A:

```http
GET /rank-challenges/{challenge_id}/tasks/{task_id}
```

후보 B:

기존 문제 목록 Response에 `saved_code` 추가.

본인 challenge에 대해서만 반환해야 한다.

---

## 10. 승급전 문제 제출

### Endpoint 후보

```http
POST /rank-challenges/{challenge_id}/tasks/{task_id}/attempts
```

### 현재 상태

미구현.

### Request 후보

```json
{
  "submitted_code": "..."
}
```

### 서버 검사

```text
JWT 사용자
→ challenge ownership
→ IN_PROGRESS
→ server now < expires_at
→ challenge task 포함 여부
→ 이미 통과한 문제 재제출 정책
→ Sandbox 채점
```

프론트가 `is_passed=true`를 보내는 구조는 사용하지 않는다.

---

## 11. 정답 처리

PASSED라면 짧은 transaction 안에서:

```text
challenge 상태/만료 재확인
→ RankChallengeTask.is_passed = true
→ 전체 합격 조건 확인
→ 필요하면 challenge SUCCESS
→ rank score 변경
→ 성공 보상
→ COMMIT
```

순서 후보.

정확한 합격 기준이 확정되기 전에는 SUCCESS 판정 코드를 임의로 만들지 않는다.

---

## 12. 오답/실패

오답 한 번으로 challenge가 바로 FAILED인지, 계속 재도전 가능한지는 정책이 필요하다.

후보:

```text
오답은 해당 문제 미통과 상태 유지
제한시간 내 재제출 가능
```

또는 기획에 따라 다른 규칙을 사용할 수 있다.

현재 문서에서는 확정하지 않는다.

---

## 13. TIMEOUT

### 기준

클라이언트 카운트다운이 아니라 서버 시각.

```text
server_now >= expires_at
AND status == IN_PROGRESS
→ TIMEOUT
```

### 현재 상태

미구현.

현재 저장 API는 만료되면 409를 반환하지만 `RANK_CHALLENGES.status`를 TIMEOUT으로 바꾸지는 않는다.

### 처리 후보

- challenge 조회/제출 시 lazy timeout 확정
- 서버 시작/정리 job에서 stale active challenge 정리

MVP에서는 복잡한 scheduler 없이 lazy 판정도 가능하다.

---

## 14. SUCCESS

SUCCESS는 **최초 상태 전환 한 번**이 보상/점수 반영의 기준이 되도록 설계한다.

```text
IN_PROGRESS → SUCCESS
```

가 성공한 transaction에서만 보상한다.

이미 SUCCESS인 challenge를 다시 처리했을 때 재화가 또 늘어나면 안 된다.

---

## 15. FAILED

### 현재 상태

정책 미정.

결정할 것:

```text
어떤 조건이 FAILED인가
실패 시 rank score 감소 여부
재도전 쿨타임
보상 여부
```

최신 상위 흐름상 성공은 보상으로 연결되고 실패는 종료 흐름이지만, 정확한 수치는 별도 확정이 필요하다.

---

## 16. 승급전 결과 조회

### Endpoint 후보

```http
GET /rank-challenges/{challenge_id}
```

### 현재 상태

전용 상세 API는 없음.

Response 후보:

```json
{
  "challenge_id": "uuid",
  "status": "SUCCESS",
  "started_at": "...",
  "expires_at": "...",
  "passed_count": "서버 계산값",
  "task_count": "서버 계산값",
  "rank_score_after": "해당 시 포함 검토"
}
```

보상 Response 필드는 실제 경제 규칙 확정 후 결정한다.

---

## 17. 재접속

현재 DB에는:

```text
challenge status
started_at
expires_at
task order
is_passed
saved_code
```

가 있으므로 서버 재시작 후에도 상당 부분 복구 가능하다.

재접속 시:

```text
challenge 조회
→ server now와 expires_at 비교
→ 만료 전이면 saved_code 복원
→ 만료됐으면 TIMEOUT 확정
```

흐름을 사용한다.

---

# D 영역 현재 완료 판정

```text
랭킹 그룹 조회            DONE
그룹 랭킹 조회            DONE
내 그룹 조회              DONE
승급전 이력 조회          DONE
승급전 시작               PARTIAL
문제 목록                 DONE
코드 저장                 DONE
실제 코드 복원            PARTIAL
문제 제출/채점            MISSING
is_passed write           MISSING
TIMEOUT 확정              MISSING
SUCCESS/FAILED            MISSING/POLICY
rank score 변경           MISSING/POLICY
성공 보상                 MISSING/POLICY
JWT ownership             MISSING
```

# 구현 전 핵심 결정

1. 한 승급전 문제 수
2. 제한시간
3. 문제 선정 주체(서버/클라이언트)
4. 합격 기준
5. 오답 후 재제출
6. 이미 통과한 문제 재제출
7. 실패 조건
8. rank score 증감
9. 성공 보상
10. 재도전 쿨타임
11. saved_code 복원 API 형태

정책이 정해지면 start Request부터 결과 API까지 한 번에 맞춘다.
