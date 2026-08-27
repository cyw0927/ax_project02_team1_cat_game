# Scenario

이 폴더는 백엔드 개발 전에 **사용자 흐름 → API 계약 → DB 변화 → 테스트**를 맞추기 위한 설계 문서 공간입니다.

문서 수가 많아져도 찾기 어렵지 않도록 루트 README는 인덱스 역할만 하고, 실제 상세 내용은 각 문서에 둡니다.

---

## 최신 제품 흐름

```text
로그인 → 홈

학습 / 배틀 / 승급전
→ 보상
→ 재화
→ 상점 / 가챠
→ 가구 / 고양이
→ 하우징
```

출석은 별도 메뉴보다 다음 자동 흐름을 기준으로 합니다.

```text
매일 자정 이후 첫 로그인
→ 자동 출석 1회
→ 100원 지급
```

상세: `00_common/13_latest_product_flow.md`

---

## 폴더

| 폴더 | 영역 |
| --- | --- |
| `00_common/` | 공통 설계, 동시성, Docker, JWT, WebSocket, 구현 현황, migration, release gate |
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

`00_common/README.md`에서 52개 공통 문서를 주제별로 찾을 수 있습니다.

```text
01~12  기본 설계
13~17  전체 흐름/실행 계획
18~22  API/상태/프론트/재화
23~27  DB 책임/권한/transaction
28~32  시간/중복/로그/설정/seed
33~37  API 운영/validation/복구
38~42  WebSocket/보상/JWT/관리자
43~47  이벤트/BackgroundTask/보안/성능/E2E
48~52  현재 코드 감사/schema gap/migration/release gate
```

현재 개발 상태를 빠르게 볼 때는 다음 5개부터 확인합니다.

- `00_common/48_current_backend_implementation_status.md`
- `00_common/49_schema_gap_register.md`
- `00_common/50_api_implementation_gap_matrix.md`
- `00_common/51_migration_change_plan.md`
- `00_common/52_mvp_backend_release_gate.md`

---

# 도메인별 문서 세트

각 영역은 가능하면 같은 순서로 읽습니다.

```text
상세 시나리오
→ API_SPEC_DRAFT.md
→ DB_BEFORE_AFTER.md
→ TEST_CASES.md
```

| 영역 | 상세 시나리오 | API 명세 | DB 변화 | 테스트 |
| --- | --- | --- | --- | --- |
| A 학습·채점 | `A-01_task_detail_view.md`, `A-02_to_A-10_detailed.md` | `01_learning_grading/API_SPEC_DRAFT.md` | `01_learning_grading/DB_BEFORE_AFTER.md` | `01_learning_grading/TEST_CASES.md` |
| B 가챠 | `B-01_to_B-10_detailed.md` | `02_gacha/API_SPEC_DRAFT.md` | `02_gacha/DB_BEFORE_AFTER.md` | `02_gacha/TEST_CASES.md` |
| C 배틀 | `C-01_to_C-10_detailed.md` | `03_battle/API_SPEC_DRAFT.md` | `03_battle/DB_BEFORE_AFTER.md` | `03_battle/TEST_CASES.md` |
| D 승급전 | `D-01_to_D-10_detailed.md` | `04_rank_challenge/API_SPEC_DRAFT.md` | `04_rank_challenge/DB_BEFORE_AFTER.md` | `04_rank_challenge/TEST_CASES.md` |
| E 인증 | `E-01_to_E-10_detailed.md` | `05_auth/API_SPEC_DRAFT.md` | `05_auth/DB_BEFORE_AFTER.md` | `05_auth/TEST_CASES.md` |
| F 하우징 | `F-01_to_F-10_detailed.md` | `06_housing/API_SPEC_DRAFT.md` | `06_housing/DB_BEFORE_AFTER.md` | `06_housing/TEST_CASES.md` |
| G 상점 | `G-01_to_G-10_detailed.md` | `07_shop/API_SPEC_DRAFT.md` | `07_shop/DB_BEFORE_AFTER.md` | `07_shop/TEST_CASES.md` |
| H 출석 | `H-01_to_H-10_detailed.md` | `08_attendance/API_SPEC_DRAFT.md` | `08_attendance/DB_BEFORE_AFTER.md` | `08_attendance/TEST_CASES.md` |

---

## 문서별 역할

**상세 시나리오**는 사용자가 화면에서 무엇을 하고 어떤 예외가 생기는지 설명합니다.

**API_SPEC_DRAFT.md**는 endpoint, Request/Response, 상태코드, 현재 구현과 미구현을 구분합니다.

**DB_BEFORE_AFTER.md**는 API 실행 전 DB와 성공/실패/rollback 후 DB를 비교합니다.

**TEST_CASES.md**는 실제 검증 항목을 `NOW / AFTER / POLICY`로 구분합니다.

---

## 작성 원칙

- 확정 요구사항과 미정 정책을 섞지 않습니다.
- 가격·확률·점수·제한시간은 기획 확정 전 임의로 고정하지 않습니다.
- 프론트 버튼 비활성화는 UX이고 실제 방어는 서버/DB에서 합니다.
- 단순 재화 차감은 가능한 경우 Atomic UPDATE를 사용합니다.
- 여러 상태를 함께 일관되게 검사해야 하는 변경은 필요한 구간에서 `SELECT ... FOR UPDATE`를 검토합니다.
- 하루 한 번처럼 유일성 자체가 규칙이면 DB UNIQUE를 최종 방어선으로 둡니다.
- Docker/LLM/WebSocket 같은 긴 작업을 DB transaction 안에서 기다리지 않습니다.
- 문서에 적혔다고 구현 완료로 표시하지 않고 실제 `main` 코드를 기준으로 `DONE / PARTIAL / MISSING / POLICY`를 구분합니다.

이 문서들의 목적은 수를 늘리는 것이 아니라 **팀원들이 서로 다른 가정으로 코드를 작성하지 않도록 같은 기준을 공유하는 것**입니다.
