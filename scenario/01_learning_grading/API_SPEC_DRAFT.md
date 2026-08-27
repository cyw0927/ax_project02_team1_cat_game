# A. 학습·채점 API 명세 초안

이 문서는 `01_learning_grading` 시나리오를 실제 HTTP API 계약으로 옮기기 위한 초안이다.

구분:

- **현재 구현**: `main` 브랜치 코드에 실제 존재
- **추가 필요**: 시나리오상 필요하지만 현재 코드에 없음
- **정책 미정**: 팀 기획이 확정돼야 Request/Response를 고정할 수 있음

가격·보상·timeout 같은 미정 숫자는 이 문서에서 임의로 정하지 않는다.

---

## 1. 개념 목록

### Endpoint

```http
GET /concepts
```

### 현재 구현

구현됨.

### Response

```json
[
  {
    "id": 1,
    "name": "함수"
  }
]
```

### DB

- `CONCEPTS` Read

### 상태코드

- `200 OK`

---

## 2. 문제 목록

### Endpoint

```http
GET /tasks
```

### 현재 구현

구현됨. `is_active=true` 문제만 반환한다.

### Response 필드

```json
[
  {
    "id": "task-uuid",
    "concept_id": 1,
    "type": "function",
    "difficulty": "...",
    "template_code": "..."
  }
]
```

### 절대 노출 금지

```text
test_cases
정답 코드
hidden expected 결과
```

### DB

- `TASKS` Read

---

## 3. 문제 상세

### Endpoint 후보

```http
GET /tasks/{task_id}
```

### 현재 상태

**추가 필요**.

### 목적

문제 하나를 클릭했을 때 목록 전체를 다시 받지 않고 해당 문제의 화면용 정보만 반환한다.

### Response 후보

```json
{
  "id": "task-uuid",
  "concept_id": 1,
  "title": "...",
  "description": "...",
  "type": "function",
  "difficulty": "...",
  "template_code": "..."
}
```

### 스키마 갭

현재 `TASKS`에는 `title`, `description` 컬럼이 없다.

이 필드가 실제 UI에 필요하다는 것이 확정된 뒤 migration을 만든다.

### 실패

- 없는 task: `404`
- inactive task: 일반 학습 진입에서는 `404` 처리 후보

---

## 4. 코드 제출 접수

### Endpoint

```http
POST /attempts
```

### 현재 구현 Request

```json
{
  "user_id": "user-uuid",
  "task_id": "task-uuid",
  "submitted_code": "...",
  "used_hint": false
}
```

### 인증 도입 후 후보

JWT에서 사용자 ID를 얻으면 body는:

```json
{
  "task_id": "task-uuid",
  "submitted_code": "...",
  "used_hint": false
}
```

처럼 줄일 수 있다.

### 현재 처리

```text
User 존재 확인
→ active Task 확인
→ TASK_ATTEMPTS PENDING INSERT
→ COMMIT
→ 202 Accepted
```

### 현재 Response

```json
{
  "attempt_id": "attempt-uuid",
  "status": "PENDING",
  "is_correct": false,
  "used_hint": false,
  "attempted_at": "..."
}
```

### 상태코드

- 정상 접수: `202 Accepted`
- 사용자 없음: `404`
- active task 없음: `404`
- Pydantic 형식 오류: `422`

### 중요한 의미

```text
202 = 채점 성공 아님
202 = 제출을 정상 접수함
```

---

## 5. 채점 결과 조회

### Endpoint

```http
GET /attempts/{attempt_id}
```

### 현재 구현

구현됨.

현재는 실제 BackgroundTask 채점이 연결되지 않아 제출 후 `PENDING`에 머물 수 있다.

### Response

```json
{
  "attempt_id": "attempt-uuid",
  "task_id": "task-uuid",
  "concept_id": 1,
  "type": "function",
  "difficulty": "...",
  "status": "PENDING",
  "is_correct": false,
  "used_hint": false,
  "attempted_at": "..."
}
```

### 추가 필요

최종 상태를 실제로 만들려면:

```text
BackgroundTask
→ Sandbox
→ test_cases 평가
→ 최종 status 저장
```

연결이 필요하다.

### 최종 status 후보

```text
PASSED
WRONG_ANSWER
RUNTIME_ERROR
TIMEOUT
SYSTEM_ERROR
```

`RUNNING`을 중간 상태로 둘지는 팀 확정 대상이다.

---

## 6. 사용자 제출 이력

### Endpoint

```http
GET /users/{user_id}/attempts
```

### 현재 구현

구현됨.

### 주의

`submitted_code` 전체는 현재 목록 Response에서 숨긴다.

JWT 적용 후 `/me/attempts` 형태를 검토할 수 있다.

---

## 7. 숙련도 조회

### Endpoint

```http
GET /users/{user_id}/proficiency
```

### 현재 구현

구현됨.

### 추가 필요

`proficiency_level`을 언제 올리거나 내리는지는 아직 비즈니스 규칙이 확정되지 않았다.

---

## 8. BackgroundTask 채점 — 내부 처리

이 부분은 외부 API가 아니라 `POST /attempts` 이후 서버 내부 흐름이다.

```text
PENDING commit
→ BackgroundTask
→ 새 DB session
→ 실행 slot 획득
→ 필요 시 RUNNING
→ Docker 실행
→ 결과 해석
→ 최종 상태 + 보상/숙련도 transaction
→ commit
```

### 확정된 Docker 제한

```text
memory 128MB
CPU 0.5
network none
filesystem read-only
```

### 현재 구현 상태

- Docker executor: 존재
- learning router 연결: 없음

---

## 9. 정답 보상

### 현재 상태

**추가 필요 + 정책 미정**.

### 필요한 원칙

- 프론트가 보상량을 보내지 않음
- 서버 기준 보상
- 같은 보상을 중복 지급하지 않음
- 채점 결과와 보상 저장의 transaction 경계 명확화

현재 어떤 문제를 몇 번까지 보상할지는 기획 확정이 필요하다.

---

## 10. 결과 오류 메시지

RUNTIME_ERROR/SYSTEM_ERROR 내용을 polling 이후에도 보여주려면 현재 `TASK_ATTEMPTS`에 저장 위치가 부족하다.

후보:

```text
result_message nullable
```

실제 UX에서 오류 메시지를 보여주기로 확정한 뒤 migration을 검토한다.

---

# A 영역 현재 완료 판정

```text
문제/개념 조회             DONE
제출 PENDING 접수          DONE
결과 polling endpoint      PARTIAL
Docker executor            DONE(미연결)
BackgroundTask 연결        MISSING
실제 채점                  MISSING
정답 보상                  MISSING/POLICY
숙련도 갱신                MISSING/POLICY
JWT 사용자 식별            MISSING
```

# 구현 전 남은 핵심 결정

1. `TASKS.test_cases` 실제 저장/해석 형식
2. 최종 status 목록
3. timeout/output cap 정확한 값
4. 정답 보상 규칙
5. 힌트 사용 시 보상
6. proficiency 변경 공식
7. title/description 필요 여부
8. result_message 저장 여부

이 항목을 확정하지 않은 상태에서 임시 숫자나 정책을 코드에 박지 않는다.
