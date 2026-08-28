# API Request / Response 예시 모음

이 문서는 A~H 시나리오를 실제 API 형태로 옮길 때 참고하기 위한 **초안 예시**다.

중요한 점은 여기 적힌 URL과 JSON이 모두 최종 확정 규칙이라는 뜻은 아니라는 것이다. 현재 구현되어 있는 API와 앞으로 추가할 API를 함께 설명하며, 아직 인증이 없는 구간에서는 `user_id`가 body/path에 들어갈 수 있다. JWT가 붙은 뒤에는 가능한 경우 로그인 사용자 ID를 토큰에서 가져오는 방향을 우선한다.

---

## 1. 문제 상세 조회

### Request

```http
GET /tasks/{task_id}
```

Body는 없다.

### 성공 Response 예시

```http
200 OK
```

```json
{
  "id": "task-uuid",
  "concept_id": 3,
  "title": "두 숫자 더하기",
  "description": "두 정수 a와 b를 더한 값을 반환하세요.",
  "type": "function",
  "difficulty": "basic",
  "template_code": "def add(a, b):\n    # 코드를 작성하세요"
}
```

### 주의

다음 데이터는 프론트에 보내지 않는다.

```text
test_cases
정답 코드
숨겨진 expected 결과
```

현재 ERD에는 `title`, `description` 컬럼이 없으므로 이 응답 형태를 사용할 경우 TASKS 컬럼 확장이 필요하다.

---

## 2. 일반 문제 코드 제출

### Request

```http
POST /attempts
```

인증 전 임시 예시:

```json
{
  "user_id": "user-uuid",
  "task_id": "task-uuid",
  "submitted_code": "def add(a, b):\n    return a + b",
  "used_hint": false
}
```

### 성공 Response

채점 결과가 아니라 **채점 접수 결과**를 반환한다.

```http
202 Accepted
```

```json
{
  "attempt_id": "attempt-uuid",
  "status": "PENDING",
  "used_hint": false
}
```

### 의미

```text
202를 받음
≠ 정답

202를 받음
= 서버가 제출을 정상 접수함
```

프론트는 `attempt_id`를 기억하고 결과 조회를 시작한다.

---

## 3. 채점 결과 조회

### Request

```http
GET /attempts/{attempt_id}
```

### 대기 중 Response 예시

```json
{
  "attempt_id": "attempt-uuid",
  "status": "PENDING",
  "is_correct": false
}
```

### 정답 Response 예시

```json
{
  "attempt_id": "attempt-uuid",
  "status": "PASSED",
  "is_correct": true,
  "reward_granted": true,
  "reward_amount": "기획 확정값"
}
```

`reward_granted`, `reward_amount`를 실제 Response에 넣을지는 API 계약 단계에서 확정한다.

### 오류 결과 예시

```json
{
  "attempt_id": "attempt-uuid",
  "status": "RUNTIME_ERROR",
  "is_correct": false,
  "message": "NameError: ..."
}
```

현재 TASK_ATTEMPTS에는 결과 메시지를 저장할 컬럼이 없으므로 재조회 시 오류 내용을 보여주려면 스키마 확장을 검토해야 한다.

---

## 4. 상점 아이템 구매

### Request

현재 인증 전 구조 예시:

```http
POST /shop/buy
```

```json
{
  "user_id": "user-uuid",
  "item_id": 5
}
```

JWT 적용 후에는 다음처럼 단순화할 수 있다.

```json
{
  "item_id": 5
}
```

### 성공 Response

```json
{
  "status": "success",
  "item_id": 5,
  "item_name": "캣타워",
  "quantity": 2,
  "current_balance": 800
}
```

### 잔액 부족

```http
409 Conflict
```

```json
{
  "detail": "Insufficient balance"
}
```

백엔드는 Python에서 `balance - price`를 계산하지 않고 DB 조건부 UPDATE를 사용한다.

---

## 5. 출석 체크

### Request

인증 전에는 다음과 같은 형태가 가능하다.

```http
POST /users/{user_id}/attendance/check-in
```

JWT 적용 후에는 `/me/attendance/check-in` 같은 구조로 바꾸는 것도 가능하다.

### 성공 Response 예시

```json
{
  "check_in_date": "2026-08-27",
  "streak_count": 4,
  "reward_amount": "기획 확정값",
  "current_balance": 1200
}
```

### 이미 출석한 경우

```http
409 Conflict
```

```json
{
  "detail": "Already checked in today"
}
```

DB의 `(user_id, check_in_date)` UNIQUE가 최종 방어선이다.

---

## 6. 가챠 실행

가챠 가격, 다회 뽑기 수, 중복 정책, 천장이 아직 최종 확정되지 않았으므로 URL과 payload는 초안으로만 본다.

### Request 예시

```http
POST /gacha/pulls
```

```json
{
  "pull_count": 1
}
```

JWT가 없을 때만 임시로 `user_id`가 추가될 수 있다.

### 성공 Response 예시

```json
{
  "results": [
    {
      "cat_id": 7,
      "name": "치즈냥이",
      "rarity": "미정"
    }
  ],
  "current_balance": 90,
  "mileage_delta": 0
}
```

중복 고양이 처리 방식이 확정되면 `duplicate`, `mileage_delta` 같은 필드를 사용할 수 있다.

---

## 7. 배틀 방 입장

### Request

```http
POST /rooms/{room_id}/join
```

임시 body 예시:

```json
{
  "user_id": "user-uuid",
  "team_name": null
}
```

### 성공 Response 예시

```json
{
  "room_id": "room-uuid",
  "participant_id": "participant-uuid",
  "status": "WAITING",
  "participant_count": 4,
  "max_participants": 4
}
```

### 방이 꽉 찬 경우

```http
409 Conflict
```

```json
{
  "detail": "Room is full"
}
```

이 API는 `ROOMS`를 짧게 `FOR UPDATE`로 잠근 뒤 현재 인원과 상태를 다시 검사하는 대표적인 비관적 락 시나리오다.

---

## 8. 배틀 Ready 변경

### Request 예시

```http
PATCH /rooms/{room_id}/participants/{participant_id}/ready
```

```json
{
  "is_ready": true
}
```

### 성공 Response

```json
{
  "participant_id": "participant-uuid",
  "is_ready": true
}
```

다른 참가자 화면에는 WebSocket 이벤트로 상태를 전달할 수 있다.

---

## 9. 배틀 시작

### Request

```http
POST /rooms/{room_id}/start
```

### 백엔드 검사

```text
요청자가 방장인가?
WAITING 상태인가?
최소 참가자 수를 충족했는가?
Ready 규칙을 충족했는가?
출제할 ROOM_TASKS가 존재하는가?
```

### 성공 Response

```json
{
  "room_id": "room-uuid",
  "status": "IN_PROGRESS"
}
```

이후 같은 방 사용자에게 게임 시작 WebSocket 이벤트를 보낼 수 있다.

---

## 10. 승급전 시작

### Request 초안

```http
POST /ranking-groups/{group_id}/rank-challenges
```

현재 구현 구조를 유지하면 body에 user/task 정보가 포함될 수 있다.

```json
{
  "user_id": "user-uuid",
  "task_ids": ["task-1", "task-2", "task-3"],
  "expires_at": "2026-08-27T10:00:00Z"
}
```

다만 최종 규칙에서 문제 수와 제한시간을 서버가 정한다면 `task_ids`, `expires_at`을 클라이언트가 지정하지 않도록 바꾸는 편이 더 안전하다.

### 성공 Response 예시

```json
{
  "challenge_id": "challenge-uuid",
  "status": "IN_PROGRESS",
  "started_at": "...",
  "expires_at": "..."
}
```

---

## 11. 승급전 코드 임시 저장

### Request

```http
PUT /rank-challenges/{challenge_id}/tasks/{task_id}/code
```

```json
{
  "saved_code": "def solution():\n    ..."
}
```

### 성공 Response

```json
{
  "challenge_id": "challenge-uuid",
  "task_id": "task-uuid",
  "saved": true
}
```

서버는 challenge가 현재 진행 중이고 아직 `expires_at`을 넘지 않았는지 검사한다.

---

## 12. 하우징 가구 배치

### Request 예시

```http
POST /users/{user_id}/house/objects
```

```json
{
  "item_id": 5,
  "position_data": {
    "x": 2,
    "y": 4,
    "rotation": 90
  }
}
```

### 성공 Response 예시

```json
{
  "placed_object_id": "placed-object-uuid",
  "item_id": 5,
  "position_data": {
    "x": 2,
    "y": 4,
    "rotation": 90
  }
}
```

현재 위치 데이터의 정확한 key와 범위는 아직 확정되지 않았다.

---

# 공통 원칙

Request/Response를 설계할 때 항상 다음 질문을 한다.

```text
1. 프론트가 정말 이 값을 보내야 하는가?
2. 서버가 토큰/DB에서 알아낼 수 있는 값은 아닌가?
3. 화면을 갱신하려면 Response에 어떤 값이 꼭 필요한가?
4. 내부 데이터(test_cases, hash, traceback)를 노출하고 있지는 않은가?
5. 같은 API를 두 번 호출하면 데이터가 어떻게 되는가?
```

이 문서의 목적은 API를 무조건 이 형태로 확정하는 것이 아니라, 기획 시나리오를 실제 HTTP 통신으로 바꾸는 방법을 팀원이 쉽게 볼 수 있게 하는 것이다.