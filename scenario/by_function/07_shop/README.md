# 07. 상점

이 폴더의 G-01~G-10, API, DB, 테스트 문서는 공통 [`사용자 중심 시나리오 보강 표준`](../00_common/54_user_centered_scenario_upgrade_standard.md)을 적용한다. 구매 매크로·가격 변경·동시 구매·commit 후 응답 유실을 다루고 조건부 원자 차감과 INVENTORIES 증가를 하나의 짧은 transaction으로 보장한다.

전체 항목별 사고·방어 연결은 [`SCENARIO_RISK_MATRIX.md`](./SCENARIO_RISK_MATRIX.md)에서 검증한다.

사용자가 상점에서 아이템을 조회하고 재화를 사용해 구매한 뒤 Inventory에 반영하는 흐름을 정리한 폴더입니다.

## 문서 읽는 순서

1. `G-01_to_G-10_detailed.md` : 상점 조회·구매·동시성·rollback 시나리오
2. `API_SPEC_DRAFT.md` : 상점 API 계약 초안
3. `DB_BEFORE_AFTER.md` : 재화 차감·Inventory 변화 전후 DB 비교
4. `TEST_CASES.md` : `NOW / AFTER / POLICY` 테스트 목록

## 현재 main 구현 상태

```text
GET /items                      DONE
GET /users/{user_id}/inventory DONE
POST /shop/buy                  DONE
서버 ITEMS.price 기준          DONE
Atomic conditional UPDATE      DONE
Inventory upsert               DONE
JWT 사용자 식별               MISSING
다수 구매/판매중지/환불        POLICY
다중 재화                      POLICY
```

## 핵심 기준

- 프론트가 가격을 보내지 않고 서버의 `ITEMS.price`를 사용합니다.
- 재화 차감은 `UPDATE ... WHERE balance >= price` 방식의 Atomic UPDATE를 사용합니다.
- 이 단순 재화 차감 시나리오에서는 `FOR UPDATE`를 기본으로 사용하지 않습니다.
- balance 차감과 Inventory upsert는 같은 transaction에서 처리합니다.
- 중간 실패 시 사용자가 돈만 잃거나 item만 얻는 반쪽 상태가 없어야 합니다.
- 동일 item 재구매는 `(user_id,item_id)` UNIQUE와 upsert로 quantity를 증가시킵니다.

주요 테이블: `USERS`, `ITEMS`, `INVENTORIES`.

현재 상점 핵심 transaction은 이미 구현돼 있으므로 재화 정책이 확정되기 전 불필요하게 구조를 다시 만들지 않습니다.
