# Scenario

이 폴더는 백엔드 개발 전에 **사용자 흐름 → API 계약 → DB 변화 → 테스트**를 맞추기 위한 설계 문서 공간입니다.

현재 요구사항 기준 문서 설계는 **완료 상태**이며, 구현 시작 전에는 먼저 다음 문서를 봅니다.

```text
00_common/53_design_completion_implementation_handoff.md
```

이후에는 새 요구사항이 생기지 않는 한 설계 파일을 계속 늘리지 않고, 실제 구현 변화에 맞춰 기존 문서를 갱신합니다.

---

## 최신 제품 흐름

```text
로그인
→ 그날 첫 로그인이라면 자동 출석 1회 + 100원
→ 홈

학습 / 배틀 / 승급전
→ 결과/보상
→ 재화
→ 상점 / 가챠
→ 가구 / 고양이
→ 하우징
```

상세 상위 기준:

- `00_common/13_latest_product_flow.md`
- `00_common/10_cross_domain_data_flow.md`

서비스 기준 timezone의 실제 값은 아직 팀 결정사항입니다.

---

## 폴더

| 폴더 | 영역 |
| --- | --- |
| `00_common/` | 공통 설계, 동시성, Docker, JWT, WebSocket, 구현 현황, migration, release gate, 최종 인수인계 |
| `01_learning_grading/` | 학습·채점 |
| `02_gacha/` | 가챠·고양이 |
| `03_battle/` | 실시간 배틀 |
| `04_rank_challenge/` | 랭킹·승급전 |
| `05_auth/` | 인증·JWT |
| `06_housing/` | 하우징 |
| `07_shop/` | 상점 |
| `08_attendance/` | 출석 |

---

# 공통 문서

`00_common/README.md`에서 **01~53 공통 문서**를 주제별로 찾을 수 있습니다.

```text
01~12  기본 설계
13~17  전체 흐름/실행 계획
18~22  API/상태/프론트/재화
23~27  DB 책임/권한/transaction
28~32  시간/중복/로그/설정/seed
33~37  API 운영/validation/복구
38~42  WebSocket/보상/JWT/관리자
43~47  이벤트/BackgroundTask/보안/성능/E2E
48~53  현재 코드 감사/schema gap/migration/release/handoff
```

구현 시작 전 핵심 문서:

- `00_common/53_design_completion_implementation_handoff.md` : **설계 종료와 실제 구현 착수 기준**
- `00_common/25_unresolved_blocker_priority.md` : 실제로 팀이 결정해야 하는 P0/P1/P2
- `00_common/48_current_backend_implementation_status.md` : 현재 main 코드 상태
- `00_common/49_schema_gap_register.md` : 19테이블로 부족한 지점
- `00_common/50_api_implementation_gap_matrix.md` : API별 DONE/PARTIAL/MISSING/POLICY
- `00_common/51_migration_change_plan.md` : migration 순서
- `00_common/52_mvp_backend_release_gate.md` : 최종 MVP 완료 기준

---

# 도메인별 문서 세트

각 영역은 다음 순서로 읽습니다.

```text
README
→ 상세 시나리오
→ API_SPEC_DRAFT.md
→ DB_BEFORE_AFTER.md
→ TEST_CASES.md
```

| 영역 | 상세 시나리오 | API 명세 | DB 변화 | 테스트 |
| --- | --- | --- | --- | --- |
| A 학습·채점 | `01_learning_grading/A-01_task_detail_view.md`, `01_learning_grading/A-02_to_A-10_detailed.md` | `01_learning_grading/API_SPEC_DRAFT.md` | `01_learning_grading/DB_BEFORE_AFTER.md` | `01_learning_grading/TEST_CASES.md` |
| B 가챠 | `02_gacha/B-01_to_B-10_detailed.md` | `02_gacha/API_SPEC_DRAFT.md` | `02_gacha/DB_BEFORE_AFTER.md` | `02_gacha/TEST_CASES.md` |
| C 배틀 | `03_battle/C-01_to_C-10_detailed.md` | `03_battle/API_SPEC_DRAFT.md` | `03_battle/DB_BEFORE_AFTER.md` | `03_battle/TEST_CASES.md` |
| D 승급전 | `04_rank_challenge/D-01_to_D-10_detailed.md` | `04_rank_challenge/API_SPEC_DRAFT.md` | `04_rank_challenge/DB_BEFORE_AFTER.md` | `04_rank_challenge/TEST_CASES.md` |
| E 인증 | `05_auth/E-01_to_E-10_detailed.md` | `05_auth/API_SPEC_DRAFT.md` | `05_auth/DB_BEFORE_AFTER.md` | `05_auth/TEST_CASES.md` |
| F 하우징 | `06_housing/F-01_to_F-10_detailed.md` | `06_housing/API_SPEC_DRAFT.md` | `06_housing/DB_BEFORE_AFTER.md` | `06_housing/TEST_CASES.md` |
| G 상점 | `07_shop/G-01_to_G-10_detailed.md` | `07_shop/API_SPEC_DRAFT.md` | `07_shop/DB_BEFORE_AFTER.md` | `07_shop/TEST_CASES.md` |
| H 출석 | `08_attendance/H-01_to_H-10_detailed.md` | `08_attendance/API_SPEC_DRAFT.md` | `08_attendance/DB_BEFORE_AFTER.md` | `08_attendance/TEST_CASES.md` |

---

## 문서별 역할

**README**는 해당 도메인의 현재 구현 상태와 문서 읽는 순서를 빠르게 보여줍니다.

**상세 시나리오**는 사용자가 화면에서 무엇을 하고 어떤 예외가 생기는지 설명합니다.

**API_SPEC_DRAFT.md**는 endpoint, Request/Response, 상태코드, 현재 구현과 미구현을 구분합니다.

**DB_BEFORE_AFTER.md**는 API 실행 전 DB와 성공/실패/rollback 후 DB를 비교합니다.

**TEST_CASES.md**는 실제 검증 항목을 `NOW / AFTER / POLICY`로 구분합니다.

---

# 현재 확정된 핵심 기준

- 출석: **매일 자정 이후 첫 로그인 자동 처리 + 100원 지급**
- Docker: **memory 128MB / CPU 0.5 / network none / read-only**
- 코드 제출: **PENDING 저장 후 202 Accepted, 긴 채점은 요청 밖에서 처리**
- 단순 재화 차감: **Atomic conditional UPDATE**
- 여러 상태의 일관성 검사: 필요한 구간 **SELECT ... FOR UPDATE**
- 하루 한 번 등 유일성 규칙: **DB UNIQUE**
- 실시간 상태: **DB commit 후 WebSocket**, DB가 최종 기준
- 인증 최종 방향: **JWT/current_user 기반**
- 가격·확률·점수·제한시간 등 미정 정책은 임의로 확정하지 않음

---

# 이제부터의 작업 방식

문서 설계는 끝났으므로 다음 순서로 진행합니다.

```text
필요한 P0 비즈니스 결정
→ 구현
→ TEST_CASES 기준 검증
→ 48/50 및 해당 도메인 문서 상태 갱신
→ E2E
→ 52 release gate
```

새 요구사항이 생기면 관련 기존 문서를 먼저 수정합니다.

**현재 요구사항 기준으로 추가 설계 문서를 더 만드는 단계는 종료되었습니다.**