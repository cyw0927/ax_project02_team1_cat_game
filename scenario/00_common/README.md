# 공통 시나리오 설계 문서

이 폴더는 `01_learning_grading`부터 `08_attendance`까지 모든 기능이 공통으로 따라야 할 설계 원칙을 모아둔 공간이다.

개별 기능 시나리오는 각 도메인 폴더에 두고, 여기에는 기능을 가로질러 같이 봐야 하는 규칙과 구현 기준을 둔다.

문서가 많아졌기 때문에 번호를 전부 한 줄씩 늘어놓기보다 **주제별 묶음**으로 찾는 것을 권장한다.

---

## 01~12. 기본 설계 원칙

- `01_business_rule_decision_checklist.md` : 확정/미정 비즈니스 규칙
- `02_api_contract_conventions.md` : Request/Response 기준
- `03_http_status_and_error_rules.md` : HTTP status/error
- `04_db_concurrency_transaction_rules.md` : Atomic Update/FOR UPDATE/UNIQUE
- `05_docker_grading_architecture.md` : Docker 채점 구조
- `06_polling_websocket_rules.md` : polling/WebSocket 역할
- `07_test_strategy.md` : 테스트 전략
- `08_team_work_and_git.md` : 3인 협업/Git
- `09_db_constraint_and_migration_checklist.md` : DB constraint/Alembic
- `10_cross_domain_data_flow.md` : 도메인 연결 흐름
- `11_implementation_order.md` : 구현 순서
- `12_definition_of_done.md` : 기능 완료 기준

---

## 13~17. 전체 제품 흐름·실행 계획

- `13_latest_product_flow.md` : 최신 제품 흐름도 기준
- `14_api_endpoint_inventory.md` : 전체 API 목록 초안
- `15_db_before_after_examples.md` : DB Before/After
- `16_test_case_matrix.md` : 핵심 테스트 매트릭스
- `17_three_person_execution_board.md` : 3인 실행 보드

---

## 18~22. API·상태·프론트·재화

- `18_api_request_response_examples.md` : API JSON 예시
- `19_failure_case_catalog.md` : 실패 케이스
- `20_state_transition_tables.md` : 상태 전이
- `21_frontend_reaction_rules.md` : 프론트 반응
- `22_reward_and_currency_write_points.md` : 보상/재화 write 지점

---

## 23~27. DB 책임·권한·트랜잭션

- `23_table_crud_matrix.md` : 19테이블 CRUD 책임
- `24_api_dependency_graph.md` : API 의존관계
- `25_unresolved_blocker_priority.md` : P0/P1/P2 개발 블로커
- `26_data_ownership_permission_matrix.md` : 데이터 ownership/권한
- `27_transaction_boundary_map.md` : transaction/commit/rollback 경계

---

## 28~32. 시간·중복·로그·설정·개발 테스트

- `28_time_timezone_policy.md` : UTC/KST/timezone
- `29_idempotency_duplicate_request_policy.md` : 중복 요청/idempotency
- `30_logging_audit_trace_policy.md` : 로그/감사/request_id
- `31_config_environment_variable_policy.md` : `.env`/설정값
- `32_seed_data_and_swagger_manual_test.md` : seed/Swagger 테스트

---

## 33~37. API 운영·검증·복구

- `33_api_version_compatibility_policy.md` : API 호환성
- `34_pagination_filter_sort_policy.md` : pagination/filter/sort
- `35_input_validation_policy.md` : 서버 validation
- `36_delete_soft_delete_policy.md` : delete/soft-delete
- `37_failure_recovery_pending_stuck_policy.md` : PENDING/RUNNING 고착 복구

---

## 38~42. 실시간·보상·인증·관리자

- `38_websocket_reconnect_state_sync.md` : WebSocket 재접속/snapshot
- `39_battle_score_duplicate_defense.md` : 배틀 중복 득점 방어
- `40_reward_exactly_once_design.md` : 보상 1회성
- `41_auth_jwt_detailed_flow.md` : JWT 상세 흐름
- `42_admin_master_data_operation_policy.md` : 관리자/master data 운영

---

## 43~47. 실시간 계약·BackgroundTask·보안·성능·E2E

- `43_websocket_event_contract.md` : WebSocket event contract
- `44_background_task_lifecycle.md` : BackgroundTask 채점 생명주기
- `45_security_abuse_rate_limit_policy.md` : 어뷰징/rate limit
- `46_db_index_performance_checklist.md` : DB index/N+1/성능
- `47_end_to_end_integration_scenarios.md` : 전체 E2E 통합 시나리오

---

## 48~52. 현재 코드 감사·스키마 갭·릴리즈 준비

- `48_current_backend_implementation_status.md` : 실제 `main` 코드 구현 현황
- `49_schema_gap_register.md` : 현재 19테이블과 최신 시나리오 사이 스키마 갭
- `50_api_implementation_gap_matrix.md` : API별 DONE/PARTIAL/MISSING/POLICY
- `51_migration_change_plan.md` : 설계 확정 후 migration 변경 순서
- `52_mvp_backend_release_gate.md` : MVP 백엔드 최종 릴리즈 게이트

---

## 현재 확정돼 있는 중요한 기준

- 출석 보상: **100원**
- 지급 시점: **매일 자정 이후 첫 로그인 시 자동 처리**
- 출석 날짜는 클라이언트 시간이 아니라 서버가 판단
- Docker: memory 128MB / CPU 0.5 / network none / read-only
- 재화 감소 단순 수치 연산은 Atomic UPDATE 우선
- 여러 상태를 함께 검사하는 변경은 필요한 구간에서 `SELECT ... FOR UPDATE`
- 하루 한 번 같은 유일성은 DB UNIQUE를 최종 방어선으로 사용
- 현재 미정인 가격/확률/점수/제한시간은 문서가 임의로 확정하지 않음

---

## 사용하는 방법

새 기능을 개발할 때 전부 읽을 필요는 없다.

예:

```text
상점 구매
→ 22 재화 write
→ 27 transaction
→ 29 중복요청
→ 35 validation
→ 50 현재 API 상태
```

```text
배틀 scoring
→ 20 상태전이
→ 38/43 WebSocket
→ 39 중복득점
→ 40 보상 1회성
→ 49 schema gap
```

```text
학습 Docker 연결
→ 05 Docker
→ 37 장애복구
→ 44 BackgroundTask
→ 48/50 현재 구현 갭
```

이 폴더는 문서를 많이 만드는 것 자체가 목적이 아니라, **코드를 만들기 전에 필요한 판단을 놓치지 않도록 하는 개발 지도**로 사용한다.
