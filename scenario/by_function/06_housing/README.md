# 06. 하우징

이 폴더의 F-01~F-10, API, DB, 테스트 문서는 공통 [`사용자 중심 시나리오 보강 표준`](../00_common/54_user_centered_scenario_upgrade_standard.md)을 적용한다. 다중 기기 배치 경쟁·배치 데이터 폭탄·저장 응답 유실과 함께 확정 기능인 공개 방문·쓰다듬기·방문 보상, 방문자 read-only/403/멱등성 및 AI 다층 방어를 검증한다.

전체 항목별 사고·방어 연결은 [`SCENARIO_RISK_MATRIX.md`](./SCENARIO_RISK_MATRIX.md)에서 검증한다.

사용자가 보유한 아이템으로 하우스를 꾸미고, 향후 고양이를 하우징과 연결하는 흐름을 정리한 폴더입니다.

## 문서 읽는 순서

1. `F-01_to_F-10_detailed.md` : 하우스 조회·배치·이동·삭제·surface 시나리오
2. `API_SPEC_DRAFT.md` : 하우징 API 계약 초안
3. `DB_BEFORE_AFTER.md` : 배치/이동/삭제 전후 DB 변화
4. `TEST_CASES.md` : `NOW / AFTER / POLICY` 테스트 목록

## 현재 main 구현 상태

```text
하우스 조회                    DONE
가구 배치                      PARTIAL
가구 이동/회전                 PARTIAL
가구 삭제                      DONE
wallpaper / floor              DONE
JWT ownership                  MISSING
position validation            POLICY/MISSING
동시 배치 race 방어            MISSING
고양이 하우징 배치             MISSING/POLICY
```

## 핵심 기준

- Inventory에 보유한 item만 배치할 수 있습니다.
- `PLACED_OBJECTS` 삭제는 하우스에서 치우는 것이며 Inventory 수량 자체를 없애는 것이 아닙니다.
- 현재 `position_data`는 JSONB 자유 구조라 x/y/rotation 규칙이 확정되면 서버 validation을 추가합니다.
- 같은 item을 동시에 여러 번 배치할 때 보유 수량을 넘는 race를 막아야 할 수 있습니다.
- 다른 사용자 집은 read-only로 조회하는 방향이 가능하지만 공개/비공개 정책은 별도 확정 대상입니다.
- 현재 `USER_CATS`에는 하우징 위치 정보가 없어 고양이 직접 배치 방식은 스키마 결정이 필요합니다.

주요 테이블: `USERS`, `ITEMS`, `INVENTORIES`, `PLACED_OBJECTS`, 고양이 연결 시 `USER_CATS`.

현재 핵심 선행 결정: 좌표/grid/rotation/겹침, 동시 배치 방어, 공개 범위, 고양이 직접 배치인지 자동 이동인지.
