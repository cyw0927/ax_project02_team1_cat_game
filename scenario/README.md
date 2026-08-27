# Scenario

이 폴더는 백엔드 개발 전에 기능별 사용자 시나리오와 해결 방법을 정리하는 공간입니다.

문서는 다음 순서로 이해할 수 있게 작성합니다.

1. 사용자가 화면에서 무엇을 하는지
2. 프론트가 백엔드에 무엇을 보내는지
3. 백엔드가 무엇을 검사하는지
4. 어떤 DB row가 읽히거나 변경되는지
5. 동시성·중복 요청을 어떻게 막는지
6. 성공/실패 응답
7. 프론트 화면 반응
8. 실제 테스트 방법

---

## 폴더 구성

- `00_common/` : 모든 기능이 함께 따라야 할 설계·검증·구현 현황 문서
- `01_learning_grading/` : 문제 조회, 제출, 비동기 채점, Docker, 보상
- `02_gacha/` : 고양이 뽑기, 재화 차감, 확률, 중복 정책
- `03_battle/` : 방, Ready, 시작, 점수, WebSocket, 종료/보상
- `04_rank_challenge/` : 랭킹, 승급전, 제한시간, 저장, 성공/실패
- `05_auth/` : 회원가입, 로그인, JWT, 권한
- `06_housing/` : 하우스, 가구 배치/이동/삭제, 벽지/바닥
- `07_shop/` : 상품 조회, 구매, Inventory, 재화 동시성
- `08_attendance/` : 자정 이후 첫 로그인 자동 출석, 100원, streak, UNIQUE

---

# 최신 전체 흐름

현재 최상위 제품 흐름 기준은:

```text
로그인
→ 홈

학습 / 배틀 / 승급전
→ 보상
→ 재화 획득
→ 상점 / 가챠
→ 가구 / 고양이
→ 하우징
```

출석은 메인 메뉴 기능이라기보다:

```text
매일 자정 이후 첫 로그인
→ 자동 출석
→ 100원 지급
```

사이드 흐름으로 본다.

자세한 기준은 `00_common/13_latest_product_flow.md`를 본다.

---

# 공통 설계 문서 찾는 법

`00_common/` 문서가 많아졌기 때문에 루트에서 52개 파일을 전부 나열하지 않는다.

`00_common/README.md`에서 다음처럼 주제별로 묶어서 찾는다.

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

특히 현재 개발 진행을 볼 때는 아래 5개를 먼저 보면 된다.

- `00_common/48_current_backend_implementation_status.md` : 실제 main 코드 구현 현황
- `00_common/49_schema_gap_register.md` : 19테이블로 부족한 지점
- `00_common/50_api_implementation_gap_matrix.md` : API별 DONE/PARTIAL/MISSING/POLICY
- `00_common/51_migration_change_plan.md` : migration 변경 순서
- `00_common/52_mvp_backend_release_gate.md` : MVP 완료 판단 기준

---

# 도메인별 API 명세 초안

시나리오를 실제 개발 계약으로 옮길 때는 각 도메인의 `API_SPEC_DRAFT.md`를 본다.

- `01_learning_grading/API_SPEC_DRAFT.md` : 학습 조회, 제출 202/PENDING, polling, BackgroundTask, Sandbox, 보상
- `02_gacha/API_SPEC_DRAFT.md` : 고양이 조회, 가챠 실행 후보, 재화 차감, 중복/천장/rollback
- `03_battle/API_SPEC_DRAFT.md` : 방/Ready/ROOM_TASKS, scoring, WebSocket, 결과/보상
- `04_rank_challenge/API_SPEC_DRAFT.md` : 랭킹 조회, 승급전 시작/저장, 채점, TIMEOUT/SUCCESS/FAILED
- `05_auth/API_SPEC_DRAFT.md` : 회원가입/로그인 후보, JWT 사용자 식별, 401/403, 자동 출석 연결
- `06_housing/API_SPEC_DRAFT.md` : 하우스 조회, 가구 CRUD, position_data, ownership, 고양이 배치 스키마 갭
- `07_shop/API_SPEC_DRAFT.md` : 아이템/Inventory 조회, Atomic 구매, upsert, rollback, JWT 전환
- `08_attendance/API_SPEC_DRAFT.md` : 현재 check-in 구현과 첫 로그인 자동 출석, 100원, UNIQUE, timezone

이 명세는 **현재 구현 / 추가 필요 / 정책 미정**을 분리해서 적는다. 문서에 endpoint 후보가 있다고 해서 코드에 구현됐다는 뜻은 아니다.

---

# 도메인별 TEST_CASES

각 도메인의 `TEST_CASES.md`는 API가 있다는 사실만 확인하지 않고 **정상/실패/동시성/rollback/권한/복구**까지 실제 검증할 항목을 모아둔다.

표기는 공통적으로 다음 의미를 사용한다.

```text
NOW     = 현재 코드로 테스트 가능
AFTER   = 해당 기능 구현 후 테스트
POLICY  = 기획 확정 후 기대값을 고정
```

- `01_learning_grading/TEST_CASES.md` : 202/PENDING, Docker, 오류/timeout, 보상 중복, test_cases 보안
- `02_gacha/TEST_CASES.md` : 재화 차감, 결과 지급, rollback, 동시 pull, 중복/천장, LLM ownership
- `03_battle/TEST_CASES.md` : 방/Ready/Start, 마지막 자리 race, 중복 득점, WebSocket, 재접속, 보상 1회성
- `04_rank_challenge/TEST_CASES.md` : challenge 생성, autosave, TIMEOUT, SUCCESS/FAILED, 점수/보상 1회성
- `05_auth/TEST_CASES.md` : 가입/로그인/JWT, 첫 로그인 자동 출석, user_id 위조, 401/403, 비밀정보
- `06_housing/TEST_CASES.md` : 소유권, 보유수량, 위치 validation, 동시 배치 race, surface, 고양이 연결
- `07_shop/TEST_CASES.md` : 서버 가격, Atomic 차감, upsert, 동시 구매, rollback, JWT ownership
- `08_attendance/TEST_CASES.md` : 100원, UNIQUE, 동시 출석, streak, 자동 로그인 출석, 자정/timezone

---

# 상세 시나리오

## A. 학습·채점

- `01_learning_grading/A-01_task_detail_view.md`
- `01_learning_grading/A-02_to_A-10_detailed.md`
- `01_learning_grading/API_SPEC_DRAFT.md`
- `01_learning_grading/TEST_CASES.md`

문제 상세, 코드 제출, PENDING, Docker 채점, 정답/오답/오류/시간초과, 재제출, 중복 보상을 다룬다.

## B. 가챠

- `02_gacha/B-01_to_B-10_detailed.md`
- `02_gacha/API_SPEC_DRAFT.md`
- `02_gacha/TEST_CASES.md`

가챠 화면, 단일/다회, 잔액 부족, 연타, 희귀도, 중복, rollback, 천장을 다룬다.

## C. 실시간 배틀

- `03_battle/C-01_to_C-10_detailed.md`
- `03_battle/API_SPEC_DRAFT.md`
- `03_battle/TEST_CASES.md`

방 목록/생성/입장, `FOR UPDATE`, Ready, 시작, 점수, WebSocket, 종료/보상을 다룬다.

## D. 승급전

- `04_rank_challenge/D-01_to_D-10_detailed.md`
- `04_rank_challenge/API_SPEC_DRAFT.md`
- `04_rank_challenge/TEST_CASES.md`

승급전 시작, 중복 시작, 문제 순서, 자동 저장, 이어하기, 제출, TIMEOUT, 성공/실패를 다룬다.

## E. 인증

- `05_auth/E-01_to_E-10_detailed.md`
- `05_auth/API_SPEC_DRAFT.md`
- `05_auth/TEST_CASES.md`

회원가입, 로그인, JWT, user_id 위조 방지, 만료와 권한, 첫 로그인 자동 출석 연결을 다룬다.

## F. 하우징

- `06_housing/F-01_to_F-10_detailed.md`
- `06_housing/API_SPEC_DRAFT.md`
- `06_housing/TEST_CASES.md`

하우스 조회, 소유권, 배치 수량, 이동/회전/삭제, 벽지/바닥, 다른 집 방문, 고양이 배치 스키마 갭을 다룬다.

## G. 상점

- `07_shop/G-01_to_G-10_detailed.md`
- `07_shop/API_SPEC_DRAFT.md`
- `07_shop/TEST_CASES.md`

상품 조회, 구매, Atomic Update, 잔액 부족, 연타, Inventory upsert, rollback과 JWT 전환을 다룬다.

## H. 출석

- `08_attendance/H-01_to_H-10_detailed.md`
- `08_attendance/API_SPEC_DRAFT.md`
- `08_attendance/TEST_CASES.md`

**자정 이후 첫 로그인 자동 출석 + 100원**, streak, 중복 요청, transaction rollback, timezone을 다룬다.

---

# 작성 원칙

- 확정 요구사항과 미정 규칙을 섞지 않는다.
- 가격·확률·점수·제한시간은 기획 확정 전 임의로 코드에 박지 않는다.
- 프론트 버튼 비활성화는 UX일 뿐 실제 방어는 서버/DB에서 한다.
- 재화 단순 차감은 가능한 경우 Atomic UPDATE를 사용한다.
- 여러 상태를 동시에 판단하는 변경은 필요한 구간에서만 `SELECT ... FOR UPDATE`를 검토한다.
- 하루 한 번 같은 규칙은 DB UNIQUE를 최종 방어선으로 둔다.
- 긴 Docker 실행/LLM 호출/WebSocket 전송을 DB transaction 안에서 기다리지 않는다.
- 문서를 만들었다고 구현됐다고 표시하지 않는다. 실제 코드를 확인해서 `DONE/PARTIAL/MISSING`을 구분한다.

> 이 폴더의 목적은 문서 수를 늘리는 것이 아니라, 3명이 동시에 백엔드를 개발할 때 서로 다른 가정을 코드에 넣는 일을 막고 실제 구현·테스트의 기준을 만드는 것입니다.
