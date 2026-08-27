# B. 가챠·고양이 API 명세 초안

이 문서는 `02_gacha` 시나리오를 실제 API 계약으로 옮기기 위한 초안이다.

현재 `main`에는 고양이 조회 API만 있고, 가챠 쓰기 API는 아직 없다. 따라서 **현재 구현**과 **추가 필요**를 분리해 적는다.

가챠 가격·확률·중복·천장·재화 종류는 아직 기획 확정 전이라 임의로 숫자를 넣지 않는다.

---

## 1. 고양이 마스터 목록

### Endpoint

```http
GET /cats
```

### 현재 구현

구현됨.

### Response

```json
[
  {
    "id": 1,
    "name": "...",
    "persona": "...",
    "rarity": "..."
  }
]
```

### DB

- `CATS` Read

### 주의

이 API가 모든 고양이를 공개할지, 현재 가챠 풀만 공개할지는 운영 정책이 필요하다.

---

## 2. 사용자 보유 고양이

### Endpoint

```http
GET /users/{user_id}/cats
```

### 현재 구현

구현됨.

### Response

```json
[
  {
    "user_cat_id": "uuid",
    "cat_id": 1,
    "name": "...",
    "persona": "...",
    "rarity": "..."
  }
]
```

### JWT 적용 후 후보

```http
GET /me/cats
```

### DB

- `USER_CATS`
- `CATS`

---

## 3. 가챠 정보 조회

### Endpoint 후보

```http
GET /gacha
```

또는

```http
GET /gacha/config
```

### 현재 상태

**미구현 / 정책 미정**.

### 화면에서 필요할 수 있는 정보

```json
{
  "single_cost": "기획 확정값",
  "currency_type": "기획 확정값",
  "multi_pull": null,
  "rarities": []
}
```

확률을 프론트에 어느 수준까지 공개할지는 기획/운영 정책에 따른다.

서버 내부 확률 원본과 프론트 표시용 데이터를 동일하게 관리하는 것이 좋지만 저장 위치는 아직 미정이다.

---

## 4. 1회 가챠

### Endpoint 후보

```http
POST /gacha/pulls
```

### Request 후보

JWT 도입 후:

```json
{
  "pull_count": 1
}
```

현재 인증이 없다면 임시로 `user_id`가 필요할 수 있으나 최종 API에서는 JWT 사용자 ID를 우선한다.

### 백엔드 처리

```text
User 확인
→ 서버 가챠 규칙/비용 조회
→ 재화 Atomic 차감
→ 서버에서 결과 추첨
→ USER_CATS 저장 또는 중복 정책 처리
→ mileage/티켓 등 확정 정책 반영
→ COMMIT
```

하나라도 실패하면 전체 rollback.

### 절대 금지

프론트가 다음을 정해서 보내게 하지 않는다.

```text
가격
당첨 cat_id
rarity
보상량
```

---

## 5. 성공 Response 후보

```json
{
  "results": [
    {
      "user_cat_id": "uuid",
      "cat_id": 7,
      "name": "...",
      "rarity": "...",
      "duplicate": false
    }
  ],
  "currency_after": "서버 최종값",
  "mileage_delta": 0
}
```

`duplicate`, `mileage_delta`는 실제 중복 정책이 확정될 때만 사용한다.

---

## 6. 잔액 부족

### 상태코드 후보

```http
409 Conflict
```

### Response 후보

```json
{
  "detail": "Insufficient currency"
}
```

### DB 결과

```text
재화 변화 없음
USER_CATS 변화 없음
```

---

## 7. 다회 가챠

### 현재 상태

**정책 미정**.

결정할 것:

```text
다회 뽑기 지원 여부
몇 회인지
비용 할인 여부
최소 희귀도 보장 여부
무료 티켓 사용 방식
```

이 값이 확정되기 전에는 `pull_count` 허용 범위를 임의로 코드에 넣지 않는다.

다회를 지원한다면 재화 차감과 모든 결과 저장을 가능한 한 하나의 transaction으로 묶는다.

---

## 8. 중복 고양이

현재 DB에는 `(user_id, cat_id)` UNIQUE가 없다.

즉 현재 구조상 같은 고양이를 여러 `USER_CATS` row로 저장할 수 있다.

정책 후보:

```text
A. 중복 고양이도 별도 개체로 소유
B. 중복이면 mileage 전환
C. 중복이면 다른 아이템/티켓 지급
```

확정 전에는 UNIQUE를 추가하지 않는다.

---

## 9. 천장

### 현재 상태

**정책 미정**.

천장을 사용하려면 최소 다음이 필요하다.

```text
누적 횟수
어떤 결과가 나오면 초기화되는지
단일/다회가 어떻게 카운트되는지
사용자별 누적 저장 위치
```

현재 19테이블 ERD에는 전용 pity counter가 없다.

MVP에서 천장을 빼면 이 스키마 문제를 뒤로 미룰 수 있다.

---

## 10. 가챠 rollback

반드시 막아야 하는 상태:

```text
재화 차감 성공
→ USER_CATS 저장 실패
→ 사용자는 돈만 잃음
```

정상 transaction:

```text
BEGIN
→ 재화 차감
→ 결과 저장
→ 부가 보상 반영
→ COMMIT
```

실패:

```text
ROLLBACK
```

---

## 11. 중복 요청/연타

사용자가 버튼을 두 번 누른 경우를 구분해야 한다.

```text
정상적인 2회 구매 의도
vs
네트워크 재전송으로 같은 요청이 두 번 도착
```

가챠는 재화가 걸린 쓰기 API라 필요하면 `idempotency key`를 검토한다.

정확한 방식은 공통 중복 요청 정책과 맞춘다.

---

## 12. 고양이 상호작용·대화

### 현재 상태

미구현.

Endpoint 후보 예:

```http
POST /users/{user_id}/cats/{user_cat_id}/chat
```

JWT 도입 후에는 user_id path를 제거하는 방향이 자연스럽다.

### 처리 원칙

```text
JWT 사용자 확인
→ USER_CAT 소유권 확인
→ CATS.persona 조회
→ CAT_MEMORIES 조회
→ 외부 LLM 호출
→ 필요한 경우 memory summary 갱신
```

LLM 호출은 긴 DB transaction 안에서 기다리지 않는다.

---

# B 영역 현재 완료 판정

```text
고양이 master 조회       DONE
내 고양이 조회           DONE
가챠 실행                MISSING
재화 차감                MISSING/POLICY
확률 추첨                MISSING/POLICY
USER_CATS 지급           MISSING
중복 처리                POLICY
천장                      POLICY
고양이 대화              MISSING
CAT_MEMORIES              MISSING
JWT 사용자 식별          MISSING
```

# 구현 전 핵심 결정

1. 가챠에서 사용하는 재화와 1회 비용
2. 희귀도/확률
3. 다회 뽑기 여부
4. 중복 고양이 처리
5. mileage 용도
6. 천장 포함 여부
7. 무료 티켓을 ITEMS/INVENTORIES로 표현할지
8. 고양이 하우징 배치 방식

이 결정이 끝난 뒤 쓰기 API와 migration을 맞춘다.
