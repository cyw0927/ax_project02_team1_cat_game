# F. 하우징 API 명세 초안

이 문서는 `06_housing` 시나리오를 실제 API 계약으로 옮기기 위한 초안이다.

현재 `main`에는 하우스 조회, 가구 배치/이동/삭제, wallpaper/floor 적용이 구현돼 있다. 다만 JWT ownership, 위치 validation, 동시 배치 race, 고양이 하우징 배치 방식은 아직 남아 있다.

---

## 1. 하우스 조회

### Endpoint

```http
GET /users/{user_id}/house
```

### 현재 구현

구현됨.

### Response

```json
{
  "house_level": 1,
  "wallpaper_item_id": 3,
  "floor_item_id": 4,
  "placed_objects": [
    {
      "placed_object_id": "uuid",
      "item_id": 10,
      "category": "furniture",
      "name": "...",
      "position_data": {
        "x": 2,
        "y": 3,
        "rotation": 90
      }
    }
  ]
}
```

현재는 임의 `user_id`의 house를 조회할 수 있으므로 다른 사용자 집 방문 기능과도 연결 가능하다.

다만 공개/비공개 정책은 별도 확정이 필요하다.

---

## 2. 내 하우스 조회 후보

JWT 도입 후 본인 집은:

```http
GET /me/house
```

형태를 검토할 수 있다.

다른 사용자 집 방문은:

```http
GET /users/{user_id}/house
```

처럼 read-only 공개 API로 유지하는 방식이 자연스럽다.

---

## 3. 가구 배치

### 현재 Endpoint

```http
POST /users/{user_id}/house/objects
```

### Request

```json
{
  "item_id": 10,
  "position_data": {
    "x": 2,
    "y": 3,
    "rotation": 90
  }
}
```

### 현재 처리

```text
User 존재
→ Inventory에 item 보유 확인
→ wallpaper/floor가 아닌지 확인
→ 같은 item의 현재 배치 개수 계산
→ 배치 개수 < 보유 quantity 확인
→ PLACED_OBJECTS INSERT
→ COMMIT
```

### 현재 상태

**PARTIAL**.

소유권과 개수는 검사하지만 `position_data` 내부 구조는 사실상 자유 dict다.

---

## 4. JWT 적용 후 배치

최종 후보:

```http
POST /me/house/objects
```

또는 기존 URL을 유지하더라도 `user_id`와 JWT 사용자가 같은지 반드시 검사한다.

프론트가 다른 사용자 UUID를 넣어 타인의 집을 수정할 수 없어야 한다.

---

## 5. position_data

현재 DB는 JSONB다.

최종적으로 다음 구조가 실제 UI에서 쓰인다면 서버 validation을 맞춘다.

```json
{
  "x": 2,
  "y": 3,
  "rotation": 90
}
```

결정할 것:

```text
x/y 자료형
허용 좌표 범위
rotation 허용값
격자 단위
가구 겹침 허용 여부
```

JSONB 자체는 유지할 수 있으므로 validation만으로 해결 가능한 부분도 있다.

---

## 6. 동시 배치 race

현재 로직은:

```text
Inventory.quantity 조회
→ placed_count 조회
→ INSERT
```

순서다.

같은 사용자가 같은 item을 동시에 여러 번 배치하면 둘 다 `placed_count < quantity`를 보고 수량을 초과할 가능성이 있다.

엄격히 막기로 확정하면 후보:

```text
해당 Inventory row SELECT ... FOR UPDATE
→ quantity / placed_count 재검사
→ INSERT
→ COMMIT
```

현재 코드는 이 race를 아직 막지 않는다.

---

## 7. 가구 이동/회전

### Endpoint

```http
PATCH /users/{user_id}/house/objects/{placed_object_id}
```

### 현재 Request

```json
{
  "position_data": {
    "x": 4,
    "y": 3,
    "rotation": 180
  }
}
```

### 현재 구현

해당 `placed_object_id`가 user 소유인지 확인하고 `position_data` 전체를 교체한다.

현재는 이동과 회전을 하나의 PATCH로 처리할 수 있다.

### 남음

- JWT ownership
- position schema
- 경계/충돌 validation

---

## 8. 가구 삭제

### Endpoint

```http
DELETE /users/{user_id}/house/objects/{placed_object_id}
```

### 현재 구현

구현됨.

삭제 대상이 해당 사용자 소유인지 확인하고 `PLACED_OBJECTS` row만 삭제한다.

### 중요한 의미

```text
하우스에서 치움
≠
Inventory에서 아이템 제거
```

Inventory quantity는 그대로 유지한다.

---

## 9. wallpaper 적용

### Endpoint

```http
PUT /users/{user_id}/house/wallpaper
```

### Request

```json
{
  "item_id": 3
}
```

### 현재 처리

```text
User 존재
→ Inventory 소유 확인
→ ITEMS.category == wallpaper
→ USERS.wallpaper_item_id 변경
→ COMMIT
```

구현됨.

---

## 10. floor 적용

### Endpoint

```http
PUT /users/{user_id}/house/floor
```

wallpaper와 동일한 구조이며 `category == floor`를 검사한다.

구현됨.

---

## 11. 소유하지 않은 아이템

현재 `_get_owned_item`에서 Inventory quantity가 1 이상인 row를 찾지 못하면 `409`를 반환한다.

이 경우:

```text
PLACED_OBJECTS 생성 없음
USERS surface 변경 없음
```

이어야 한다.

---

## 12. 다른 사용자 집 방문

현재 `GET /users/{user_id}/house` 자체가 다른 사용자 집 조회를 허용한다.

MVP 공개 하우스라면 별도 endpoint 없이 이 API를 사용할 수 있다.

향후 privacy가 생기면:

```text
public/private 상태
방문 허용 범위
```

를 추가 설계해야 한다.

현재 ERD에는 privacy 상태가 없다.

---

## 13. 고양이 하우징 배치

최신 제품 흐름에는:

```text
가챠
→ 고양이 획득
→ 하우징에 배치
```

가 있다.

현재 스키마는:

```text
PLACED_OBJECTS → item_id
USER_CATS → user_id, cat_id
```

뿐이라 고양이 위치를 저장할 곳이 없다.

### 현재 상태

**MISSING / POLICY / SCHEMA GAP**.

후보:

```text
A. USER_CATS에 position_data 추가
B. 고양이는 직접 배치하지 않고 자동 노출/이동
C. 별도 placement 구조
```

20개 미만 테이블 제한을 고려하면 기존 USER_CATS 확장도 후보지만 UI 동작을 먼저 확정한다.

---

## 14. 고양이 상호작용

하우징에서 고양이를 눌러 대화하는 UX라면 실제 API 책임은 cats 도메인과 연결한다.

```text
하우징 UI에서 user_cat 선택
→ cats chat API
→ persona/memory/LLM 처리
```

하우징 transaction과 긴 LLM 호출을 묶지 않는다.

---

# F 영역 완료 판정

```text
하우스 조회                 DONE
가구 배치                   PARTIAL
가구 이동/회전              PARTIAL
가구 삭제                   DONE
wallpaper                    DONE
floor                        DONE
다른 집 read-only 조회       DONE에 가까움
JWT ownership               MISSING
position validation         POLICY/MISSING
동시 배치 race 방어         MISSING
고양이 하우징 배치          MISSING/POLICY
privacy                     POLICY
```

# 구현 전 핵심 결정

1. `position_data` 정확한 구조
2. x/y 범위와 grid
3. rotation 값
4. 겹침 허용 여부
5. 동시 배치 race를 서버에서 엄격히 막을지
6. 공개 하우스 범위
7. 고양이 직접 배치인지 자동 이동인지
8. house_level 실제 기능

현재 구현을 유지하면서도 위 정책이 확정될 때 필요한 부분만 좁게 보완한다.
