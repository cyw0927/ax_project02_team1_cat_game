# 02. 가챠·고양이

이 폴더의 B-01~B-10, API, DB, 테스트 문서는 공통 [`사용자 중심 시나리오 보강 표준`](../00_common/54_user_centered_scenario_upgrade_standard.md)을 적용한다. 버튼 매크로·동시 차감·응답 유실·애니메이션 중 종료와 실제 지급 복구를 연결하며 가격·단회/다회·확률·천장·중복/mileage는 `TBD`로 보호한다.

전체 항목별 사고·방어 연결은 [`SCENARIO_RISK_MATRIX.md`](./SCENARIO_RISK_MATRIX.md)에서 검증한다.

사용자가 재화를 사용해 고양이를 획득하고 소유 데이터에 반영하는 흐름을 정리한 폴더입니다.

## 문서 읽는 순서

1. `B-01_to_B-10_detailed.md` : 가챠 사용자 시나리오
2. `API_SPEC_DRAFT.md` : 가챠/고양이 API 계약 초안
3. `DB_BEFORE_AFTER.md` : 재화 차감·결과 저장·rollback 전후 DB 변화
4. `TEST_CASES.md` : `NOW / AFTER / POLICY` 테스트 목록

## 현재 main 구현 상태

```text
GET /cats                       DONE
GET /users/{user_id}/cats       DONE
가챠 실행 API                   MISSING
재화 차감 + USER_CATS 저장      MISSING/POLICY
중복 고양이 처리                POLICY
천장                            POLICY
고양이 대화/CAT_MEMORIES         MISSING
```

## 핵심 기준

- 가격, 당첨 결과, 희귀도는 프론트가 정하지 않고 서버가 결정합니다.
- 재화 차감과 고양이/중복 보상 저장은 같은 transaction으로 처리합니다.
- 저장 실패 시 사용자가 재화만 잃는 상태가 없어야 합니다.
- 동시 가챠에서도 잔액이 음수가 되면 안 됩니다.
- 중복 고양이, mileage, 천장, 무료 티켓 구조는 기획 확정 전 코드/DB에 임의로 고정하지 않습니다.

주요 테이블: `USERS`, `CATS`, `USER_CATS`, 필요 시 `CAT_MEMORIES`.

현재 가장 큰 선행 결정은 **가챠 재화/비용, 확률, 중복 처리, 천장 여부**입니다.
