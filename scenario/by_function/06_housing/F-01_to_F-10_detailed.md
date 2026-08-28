# F-01 ~ F-10. 하우징 상세 시나리오

이 문서는 사용자가 자신의 집을 조회하고, 인벤토리 가구를 배치·이동·회전·삭제하고, 벽지/바닥을 바꾸는 흐름을 정리한다.

> 현재 `position_data`의 정확한 x/y/rotation 형식, 방 크기, 충돌 규칙은 아직 확정되지 않았다.

---

# F-01. 내 하우스 진입

## 목적
사용자가 자신의 집 화면을 열었을 때 배경과 배치된 가구를 한 번에 렌더링할 수 있게 한다.

## 흐름
```text
하우징 메뉴 클릭
→ 현재 user 확인
→ USERS에서 house_level/wallpaper/floor 조회
→ PLACED_OBJECTS 조회
→ ITEMS와 JOIN해 이름/종류 확인
→ 화면 렌더링용 데이터 반환
```

## DB
- `USERS`
- `PLACED_OBJECTS`
- `ITEMS`

## 변경
없음. 조회만 한다.

## Lock
필요 없다.

---

# F-02. 가구 인벤토리 열기

## 목적
현재 사용자가 실제로 소유한 배치 가능한 물건만 꾸미기 목록에 보여준다.

## 흐름
```text
꾸미기 버튼 클릭
→ INVENTORIES에서 quantity>0 조회
→ ITEMS JOIN
→ category 확인
→ 가구/소품 목록 반환
```

## 왜 Inventory를 기준으로 하나
ITEMS는 상점 마스터 데이터라서 모든 상품이 들어 있다. 사용자가 실제로 가진 것은 INVENTORIES가 증명한다.

## 화면 표시 후보
- item 이름
- 보유 quantity
- 현재 배치 수
- 추가 배치 가능한 수

## 테스트
- 아무것도 보유하지 않은 사용자
- 동일 아이템 여러 개 보유
- wallpaper/floor가 일반 가구 목록에 섞이지 않는지

---

# F-03. 가구 정상 배치

## 목적
사용자가 보유한 가구를 집의 특정 위치에 놓는다.

## Request 형태 예시
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

정확한 position schema는 아직 확정 전이다.

## 백엔드 검사
1. 현재 user 확인
2. item 존재 확인
3. item category가 배치 가능한 종류인지 확인
4. INVENTORIES에 소유 수량이 있는지 확인
5. 같은 item의 현재 배치 수가 quantity보다 적은지 확인
6. position_data 형식/범위를 검증
7. `PLACED_OBJECTS` INSERT

## DB
- `ITEMS`
- `INVENTORIES`
- `PLACED_OBJECTS`

## 동시성 주의
같은 가구 1개를 가지고 동시에 두 배치 요청을 보내면 두 요청이 모두 `현재 배치 0개`를 볼 가능성이 있다. 수량을 엄격히 보장하려면 배치 검사 구간을 직렬화하거나 다른 DB 방어를 검토해야 한다.

## 테스트
- 정상 1개 배치
- quantity만큼 정확히 배치
- quantity 초과 시도
- 같은 순간 두 번 배치

---

# F-04. 보유하지 않은 가구 배치

## 상황
사용자가 API를 직접 조작해 상점에서 사지 않은 `item_id`를 보낸다.

## 처리
```text
INVENTORIES 조회
→ quantity>0 row 없음
→ PLACED_OBJECTS를 만들지 않음
→ 409/403 등 정책 응답
```

## 왜 프론트를 믿으면 안 되나
화면에 없는 버튼도 API 직접 호출로 요청할 수 있다. 소유권은 서버가 반드시 DB로 재확인한다.

## DB 변경
없음.

## 테스트
다른 user가 가진 item을 내 집에 배치하려는 요청도 실패해야 한다.

---

# F-05. 보유 수량 초과 배치

## 예
캣타워를 1개 샀는데 같은 item을 집에 2개 놓으려 한다.

## 검사
```text
inventory.quantity = 1
현재 placed_count = 1
→ placed_count < quantity 조건 실패
→ 추가 배치 거부
```

## 핵심
`INVENTORIES.quantity`는 소유 수량이고 `PLACED_OBJECTS` 행 수는 현재 집에 꺼내놓은 수량이다.

삭제(치우기)를 하면 inventory 수량은 그대로이고 placed_count만 줄어든다.

## 동시성
F-03에서 설명한 동시 배치 race condition을 반드시 테스트한다.

---

# F-06. 가구 이동

## 목적
이미 배치된 object의 위치만 바꾼다.

## 흐름
```text
사용자 드래그
→ PATCH /house/objects/{placed_object_id}
→ 해당 object가 현재 user 소유인지 확인
→ 새 position_data 검증
→ UPDATE
→ COMMIT
```

## 보안
다른 사람의 `placed_object_id`를 넣어 움직이지 못하게 `user_id` 소유권 검사를 반드시 한다.

## 미정
- 방 밖 좌표 거부 기준
- 다른 가구와 겹침 허용 여부
- 서버가 충돌을 검사할지 프론트에 맡길지

### 추천 MVP
격자 밖 여부는 서버가 검사하고 복잡한 충돌 판정은 우선 프론트에서 처리하는 방식이 단순하다. 기획 확정 후 결정한다.

---

# F-07. 가구 회전

## 목적
가구의 위치는 유지하면서 방향만 변경한다.

## 방법
`position_data`에 rotation을 포함시키는 안이라면 이동 API와 같은 PATCH를 재사용할 수 있다.

예:
```json
{
  "position_data": {
    "x": 2,
    "y": 4,
    "rotation": 180
  }
}
```

## 결정 필요
허용 rotation을 임의 숫자로 둘지:
```text
0, 90, 180, 270
```
처럼 제한할지 정해야 한다.

격자형 2D 하우징이라면 90도 단위 제한이 단순하지만 UI 디자인에 따라 달라질 수 있다.

## 테스트
- 허용 rotation
- 허용하지 않는 값
- 다른 user object 회전

---

# F-08. 가구 치우기

## 목적
가구를 집에서 제거하되 사용자가 구매한 소유권 자체는 유지한다.

## 처리
```text
치우기 클릭
→ placed_object 소유권 확인
→ PLACED_OBJECTS DELETE
→ INVENTORIES 변경 없음
→ COMMIT
```

## 초보자 핵심
```text
PLACED_OBJECTS 삭제 = 방에서 치움
INVENTORIES 삭제 = 물건 자체를 잃음
```
둘은 완전히 다르다.

## 테스트
치운 뒤 인벤토리에 같은 아이템이 다시 배치 가능한 상태인지 확인한다.

---

# F-09. 벽지/바닥 변경

## 목적
일반 가구처럼 PLACED_OBJECTS에 놓지 않고 USERS의 현재 배경 설정을 바꾼다.

## 흐름
```text
사용자가 벽지 선택
→ INVENTORIES에서 소유 확인
→ ITEMS.category가 wallpaper인지 확인
→ USERS.wallpaper_item_id UPDATE
```

바닥은 `floor_item_id`로 동일하게 처리한다.

## 왜 category 확인이 필요한가
캣타워 item_id를 wallpaper_item_id에 넣는 API 조작을 막기 위해서다.

## DB
- `USERS`
- `INVENTORIES`
- `ITEMS`

## 테스트
- 정상 wallpaper
- 정상 floor
- 보유하지 않은 wallpaper
- furniture를 wallpaper로 설정 시도

---

# F-10. 다른 사용자의 하우스 방문

## 목적
공개 하우스가 허용된다면 다른 사용자 집은 **읽기 전용**으로 보여준다.

## 흐름
```text
대상 user_id 선택
→ USERS 배경 조회
→ PLACED_OBJECTS 조회
→ ITEMS JOIN
→ 화면 렌더링
```

## 중요한 권한
조회가 가능하더라도 다음 API는 대상 user 본인만 가능해야 한다.
- 가구 배치
- 이동
- 회전
- 삭제
- 벽지/바닥 변경

## 현재 ERD 한계
하우스 공개/비공개 상태를 저장하는 컬럼이 없다. 모든 집을 공개로 할지, 공개 설정이 필요할지 기획에서 결정해야 한다.

## 테스트
- 다른 집 조회
- 다른 집 object 수정 시도 → 거부
- 존재하지 않는 user 집 조회

---

# F 영역에서 팀이 확정해야 할 것

1. `position_data` 정확한 JSON 구조
2. x/y의 허용 범위
3. 격자 크기
4. rotation 허용값
5. 가구 충돌/겹침 허용 여부
6. 충돌을 서버가 검사할지 프론트가 처리할지
7. 같은 item의 동시 배치 수량 방어 방식
8. `house_level`이 실제로 무엇을 바꾸는지
9. 다른 사용자 집 공개 여부
10. 하우스 공개/비공개 컬럼 추가 필요 여부
