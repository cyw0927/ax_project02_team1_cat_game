# F. 하우징 테스트 케이스

표기:

- **NOW**: 현재 코드로 테스트 가능
- **AFTER**: 보완 구현 후 테스트
- **POLICY**: 위치/충돌/공개범위/고양이 배치 규칙 확정 후 기대값 고정

---

## F-T01. 내/다른 사용자 하우스 조회 — NOW

`GET /users/{user_id}/house`

**Then**
- 존재하는 user는 house_level/surface/placed_objects 반환
- 없는 user는 `404`
- 조회만으로 DB 변경 없음

---

## F-T02. 정상 가구 배치 — NOW

Inventory에 quantity가 충분한 일반 가구를 배치한다.

**Then**
- `201`
- PLACED_OBJECTS 1개 생성
- Inventory quantity는 감소하지 않음

---

## F-T03. 미보유 가구 배치 — NOW

Inventory에 없는 item이면 `409`, PLACED_OBJECTS 생성 없음.

---

## F-T04. wallpaper/floor 일반 오브젝트 배치 거절 — NOW

surface category를 `/house/objects`로 넣으면 거절해야 한다.

---

## F-T05. 보유 수량 초과 배치 — NOW

quantity=1인 item을 이미 1개 배치한 뒤 다시 배치하면 `409`.

---

## F-T06. 동시 수량 초과 race — AFTER

quantity=1인 같은 item을 동시에 여러 번 배치한다.

**Then** 최종 PLACED_OBJECTS 수가 quantity를 넘지 않아야 한다.

현재 구현은 `quantity 조회 → placed_count 조회 → INSERT`라 race 가능성이 있으므로 보완 후 필수 테스트.

---

## F-T07. 정상 이동/회전 — NOW/PARTIAL

본인 placed_object의 `position_data`를 PATCH하면 새 값으로 교체된다.

정확한 x/y/rotation validation은 POLICY.

---

## F-T08. 타인 오브젝트 수정 — NOW/AFTER JWT

현재 URL user_id와 placed_object ownership이 다르면 `404`.

JWT 이후에는 path user_id 위조 자체로 타인 집 수정이 불가능해야 한다.

---

## F-T09. position_data 형식 — AFTER/POLICY

구조 확정 후 다음을 검증한다.

- 필수 x/y/rotation 여부
- 자료형
- 허용 범위
- rotation 허용값
- 여분/이상 필드 처리

---

## F-T10. 격자/경계 — AFTER/POLICY

집 밖 좌표나 허용하지 않는 grid 값을 서버가 거절하기로 했다면 DB에 저장되지 않아야 한다.

---

## F-T11. 가구 겹침 — AFTER/POLICY

겹침을 금지한다면 충돌 위치 배치/이동을 거절한다.

프론트만 막고 서버가 아무 값이나 저장하는 구조로 할지 여부를 먼저 확정한다.

---

## F-T12. 가구 제거 — NOW

본인 placed_object를 DELETE하면 PLACED_OBJECTS row만 사라지고 Inventory quantity는 유지되어야 한다.

---

## F-T13. wallpaper 정상 적용 — NOW

보유 item + category=wallpaper이면 USERS.wallpaper_item_id가 변경된다.

---

## F-T14. floor 정상 적용 — NOW

보유 item + category=floor이면 USERS.floor_item_id가 변경된다.

---

## F-T15. 잘못된 surface category — NOW

floor item을 wallpaper API에 보내거나 반대의 경우 `409`, USERS surface 값 변화 없음.

---

## F-T16. 공개 하우스 — NOW/POLICY

현재 API는 다른 user_id 집 조회가 가능하다.

MVP 공개 하우스로 확정하면 read-only 방문이 계속 가능해야 하고, privacy를 도입하면 그 정책에 맞게 테스트를 변경한다.

---

## F-T17. 고양이 하우징 표시/배치 — AFTER/POLICY

UI/스키마 확정 후:

- 본인 USER_CAT만 표시/배치
- 위치 저장 방식 일치
- 타인 USER_CAT 배치 불가
- 고양이 소유 데이터와 하우징 표현이 일관됨

현재 저장 구조가 없으므로 SCHEMA GAP 해결 전 테스트를 DONE 처리하지 않는다.

---

## F-T18. 고양이 상호작용 연결 — AFTER

하우징에서 user_cat 선택 후 cats chat API로 이어지되, 하우징 DB transaction과 LLM 호출을 묶지 않는지 확인한다.

---

# F 완료 기준

```text
소유권
→ 보유수량
→ 위치 validation
→ 동시 배치 방어
→ surface
→ 공개 조회
→ 고양이 연결
```

중 실제 MVP 범위까지 검증한다.
