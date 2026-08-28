# F. 하우징 DB Before / After

이 문서는 가구 배치·이동·삭제와 wallpaper/floor 적용이 **Inventory 소유권과 PLACED_OBJECTS를 어떻게 사용해야 하는지** 정리한다.

현재 가구 CRUD는 구현돼 있지만 위치 규칙, JWT ownership, 동시 배치 race, 고양이 배치 방식은 남아 있다.

---

## F-DB01. 하우스 조회 — 현재

### Before

```text
USERS.U1
wallpaper_item_id=W1
floor_item_id=F1

PLACED_OBJECTS
P1 user=U1 item=I10 position_data={...}
```

### API

```http
GET /users/U1/house
```

### After

DB 변화 없음.

USERS surface 값과 U1의 PLACED_OBJECTS를 읽어 반환한다.

---

## F-DB02. 정상 가구 배치 — 현재

### Before

```text
INVENTORIES
user=U1 item=I10 quantity=2

PLACED_OBJECTS
U1/I10 배치 수=1
```

### 처리

```text
User 확인
→ Inventory 소유 확인
→ category 확인
→ placed_count 확인
→ 1 < 2
→ PLACED_OBJECTS INSERT
→ COMMIT
```

### After

```text
INVENTORIES.quantity = 2   # 그대로
PLACED_OBJECTS U1/I10 배치 수 = 2
```

하우스에서 배치한다고 Inventory 수량을 소비하는 것이 아니다.

---

## F-DB03. 미보유 가구

### Before

U1의 Inventory에 I20 없음.

### After

```text
PLACED_OBJECTS 변화 없음
INVENTORIES 변화 없음
```

---

## F-DB04. 보유량 초과 배치 — 현재 단일 요청

### Before

```text
Inventory quantity=1
PlacedObject count=1
```

### 새 배치 요청

### After

새 PLACED_OBJECTS row 없음.

---

## F-DB05. 동시 배치 race — 보완 필요

### Before

```text
Inventory quantity=1
PlacedObject count=0
```

Request A와 B가 동시에 실행.

### 현재 위험

둘 다:

```text
quantity=1 확인
placed_count=0 확인
```

후 각각 INSERT할 수 있다.

### 올바른 After 목표

```text
PlacedObject count <= Inventory.quantity
```

엄격히 막는다면 해당 Inventory row lock 후 count를 재검사하는 방법을 검토한다.

---

## F-DB06. 가구 이동/회전 — 현재

### Before

```text
P1.position_data = old
P1.user_id = U1
```

### 처리

ownership 확인 후 `position_data` UPDATE.

### After

```text
P1.position_data = new
```

Inventory와 다른 PLACED_OBJECTS는 변화 없음.

---

## F-DB07. 타인 오브젝트 이동

### Before

```text
P1.user_id=U2
```

U1이 P1 수정 시도.

### After

```text
P1 변화 없음
```

JWT 적용 후에는 Request URL의 user_id보다 current_user ownership을 기준으로 한다.

---

## F-DB08. 위치 validation 실패 — 향후

위치 구조가 확정된 뒤 잘못된 좌표/회전을 받으면 DB UPDATE/INSERT 전에 거절한다.

### After

```text
기존 position_data 유지
새 PLACED_OBJECTS 없음
```

---

## F-DB09. 가구 제거 — 현재

### Before

```text
Inventory U1/I10 quantity=2
PlacedObject P1 user=U1 item=I10
```

### 처리

P1 DELETE → COMMIT.

### After

```text
P1 없음
Inventory quantity=2   # 그대로
```

`하우스에서 치움`과 `아이템 소유권 삭제`를 구분한다.

---

## F-DB10. wallpaper 적용 — 현재

### Before

```text
Inventory U1/W1 quantity>0
ITEMS.W1.category=wallpaper
USERS.U1.wallpaper_item_id=old
```

### After

```text
USERS.U1.wallpaper_item_id=W1
Inventory 변화 없음
```

---

## F-DB11. floor 적용 — 현재

wallpaper와 동일하다.

### After

```text
USERS.U1.floor_item_id=F1
Inventory 변화 없음
```

---

## F-DB12. 잘못된 surface category

floor item을 wallpaper endpoint로 요청하는 경우.

### After

```text
USERS.wallpaper_item_id 변화 없음
Inventory 변화 없음
```

---

## F-DB13. 공개 하우스 조회

다른 사용자 U2가 U1의 공개 house를 읽는 경우:

### After

DB 변화 없음.

읽기 API만으로 방문 기록을 만들지 않는다. 방문 기록이 실제 요구되면 별도 스키마 검토가 필요하다.

---

## F-DB14. 고양이 하우징 배치 — 스키마 갭

현재:

```text
PLACED_OBJECTS → item_id
USER_CATS → user_id, cat_id
```

이므로 고양이 좌표를 저장하지 못한다.

### 후보 A

`USER_CATS.position_data` 같은 기존 테이블 확장.

### 후보 B

고양이는 위치 저장 없이 하우스에서 자동 노출/움직임.

### 후보 C

별도 placement 구조.

어느 방식도 현재 확정하지 않는다.

### After 목표

어떤 방식을 택하든:

```text
본인이 소유한 USER_CAT만 하우스에 표시/배치
타인 USER_CAT 상태는 변화 없음
```

이어야 한다.

---

## F-DB15. 고양이 상호작용

하우징 화면에서 고양이를 눌러 대화해도 가구 위치 transaction과 CAT_MEMORIES/LLM 호출을 하나의 긴 transaction으로 묶지 않는다.

### After

가구/Inventory/하우스 surface는 대화 실패로 인해 rollback되지 않는다.

---

# 한눈에 보는 핵심

```text
Inventory = 소유 수량
PlacedObjects = 현재 하우스에 놓인 가구

배치
소유 수량 확인 → 배치 row 추가
Inventory 수량은 그대로

제거
배치 row 삭제
Inventory는 그대로

동시 배치
보유 수량 초과 race 방어 필요

고양이 배치
현재 스키마 갭 → UI 방식 확정 후 결정
```

하우징 DB에서는 **소유권과 화면 배치 상태를 같은 것으로 착각하지 않는 것**이 가장 중요하다.
