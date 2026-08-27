# 공통 시나리오 설계 문서

이 폴더는 `01_learning_grading`부터 `08_attendance`까지 모든 기능이 공통으로 따라야 할 설계 원칙을 모아둔 임시 문서 공간이다.

각 기능 폴더에는 개별 시나리오가 들어가고, 이 폴더에는 기능을 가로질러 같이 결정해야 하는 규칙을 적는다.

예를 들어 다음과 같은 내용이다.

- 어떤 비즈니스 규칙을 팀이 먼저 결정해야 하는가
- Request/Response는 어떤 기준으로 정하는가
- HTTP 상태코드와 오류 응답은 어떻게 통일하는가
- 재화 변경, 방 입장, 출석 같은 동시성 문제를 어떤 방식으로 막는가
- Docker 채점기는 어떤 자원 제한을 가져야 하는가
- polling과 WebSocket은 어디에서 사용하는가
- 테스트는 정상/예외/동시성 중 무엇을 확인해야 하는가
- 3명이 동시에 개발할 때 어떤 순서로 branch/PR을 나누는가
- DB UNIQUE, FK, migration은 언제 확정하는가

## 문서 목록

1. `01_business_rule_decision_checklist.md` : 코딩 전에 반드시 결정해야 하는 비즈니스 규칙
2. `02_api_contract_conventions.md` : API Request/Response 설계 공통 기준
3. `03_http_status_and_error_rules.md` : HTTP 상태코드와 오류 응답 기준
4. `04_db_concurrency_transaction_rules.md` : Atomic Update, FOR UPDATE, UNIQUE, transaction 사용 기준
5. `05_docker_grading_architecture.md` : Docker SDK 기반 채점 구조와 제한사항
6. `06_polling_websocket_rules.md` : polling과 WebSocket의 역할 구분
7. `07_test_strategy.md` : 정상/예외/동시성/통합 테스트 기준
8. `08_team_work_and_git.md` : 3인 분업과 Git 협업 방식
9. `09_db_constraint_and_migration_checklist.md` : DB 제약과 Alembic 변경 시 확인사항
10. `10_cross_domain_data_flow.md` : 학습·경제·배틀·랭킹 등 도메인 간 연결 흐름
11. `11_implementation_order.md` : 실제 구현 우선순위와 선행조건
12. `12_definition_of_done.md` : 기능 하나를 완료했다고 판단하는 기준

> 이 문서들은 현재 설계용 초안이다. 미정 숫자나 정책은 임의로 확정하지 않는다.