# Scenario

이 폴더는 백엔드 개발 전에 기능별 사용자 시나리오와 해결 방법을 임시로 정리하기 위한 공간입니다.

단순히 API 이름만 적는 것이 아니라, 각 기능을 다음 순서로 이해할 수 있게 기록합니다.

1. 사용자가 화면에서 무엇을 하는지
2. 프론트엔드가 백엔드에 무엇을 보내는지
3. 백엔드가 무엇을 검사하는지
4. 어떤 DB 테이블을 읽거나 변경하는지
5. 동시성·중복 요청을 어떻게 막는지
6. 성공/실패 시 어떤 응답을 보내는지
7. 프론트 화면이 어떻게 바뀌는지
8. 실제 개발 시 무엇을 테스트해야 하는지

## 폴더 구성

- `00_common/` : 모든 기능이 공통으로 따라야 할 비즈니스 규칙, API 계약, 오류, 동시성, Docker, 테스트, Git, DB migration 기준
- `01_learning_grading/` : 학습 문제 조회, 코드 제출, 비동기 채점, Docker Sandbox, 정답·오답 처리와 보상 시나리오
- `02_gacha/` : 고양이 뽑기, 재화 차감, 희귀도 추첨, 중복 고양이와 천장 정책 시나리오
- `03_battle/` : 실시간 배틀 방 생성·입장·준비·시작·점수·종료 및 WebSocket 시나리오
- `04_rank_challenge/` : 랭킹 그룹과 승급전 시작, 코드 저장, 제한시간, 성공·실패 처리 시나리오
- `05_auth/` : 회원가입, 로그인, JWT, 사용자 식별과 권한 처리 시나리오
- `06_housing/` : 하우스 조회, 가구 배치·이동·회전·삭제, 벽지·바닥 적용 시나리오
- `07_shop/` : 상점 조회, 아이템 구매, 재화 차감, Inventory 반영과 동시성 방어 시나리오
- `08_attendance/` : 출석 체크, 연속 출석, 하루 1회 보상과 UNIQUE 제약 시나리오

## 공통 설계 문서

`00_common/`에는 다음 문서가 있다.

- `01_business_rule_decision_checklist.md` : 코딩 전에 팀이 반드시 결정해야 할 미정 규칙
- `02_api_contract_conventions.md` : Request/Response와 API 계약 공통 기준
- `03_http_status_and_error_rules.md` : HTTP 상태코드와 오류 응답 통일 기준
- `04_db_concurrency_transaction_rules.md` : Atomic Update, FOR UPDATE, UNIQUE, transaction 선택 기준
- `05_docker_grading_architecture.md` : Docker SDK 기반 채점 구조와 보안/자원 제한
- `06_polling_websocket_rules.md` : 채점 polling과 배틀 WebSocket 역할 구분
- `07_test_strategy.md` : 정상/예외/동시성/rollback/통합 테스트 방법
- `08_team_work_and_git.md` : 3명 분업, branch, PR, migration 충돌 방지
- `09_db_constraint_and_migration_checklist.md` : UNIQUE/FK/NULL/CHECK/Alembic 확인사항
- `10_cross_domain_data_flow.md` : 학습·경제·가챠·배틀·승급전·인증 연결 구조
- `11_implementation_order.md` : 실제 백엔드 구현 순서와 선행조건
- `12_definition_of_done.md` : 기능 하나를 완료했다고 판단하는 기준
- `13_latest_product_flow.md` : 최신 흐름도 기준 로그인→홈→학습/배틀/승급전→재화→상점/가챠→하우징 연결
- `14_api_endpoint_inventory.md` : A~H 전체 API 엔드포인트 초안과 사용 테이블 목록
- `15_db_before_after_examples.md` : 문제 제출, 상점, 출석, 방 입장, 배틀 점수, 승급전, 가챠 등 DB Before/After 예시
- `16_test_case_matrix.md` : 핵심 정상/예외/동시성/rollback 테스트케이스 목록
- `17_three_person_execution_board.md` : A/B/C 3명 분업, 구현 순서, 필수 테스트, 리뷰 기준

## 현재 작성된 상세 시나리오

### A. 학습·채점
- `01_learning_grading/A-01_task_detail_view.md` : 문제 하나를 정상적으로 여는 과정
- `01_learning_grading/A-02_to_A-10_detailed.md` : 코드 제출, PENDING 대기, Docker 채점, 정답·오답·오류·시간초과, 재제출, 중복 보상 방어

### B. 가챠
- `02_gacha/B-01_to_B-10_detailed.md` : 가챠 화면, 1회/다회 뽑기, 잔액 부족, 연타, 희귀도, 중복, rollback, 천장

### C. 실시간 배틀
- `03_battle/C-01_to_C-10_detailed.md` : 방 목록/생성/입장, FOR UPDATE, Ready, 시작, 점수, 오답, 종료

### D. 승급전
- `04_rank_challenge/D-01_to_D-10_detailed.md` : 승급전 진입/시작, 중복 시작, 문제 조회, 자동 저장, 이어하기, 제출, TIMEOUT, 성공/실패

### E. 인증
- `05_auth/E-01_to_E-10_detailed.md` : 회원가입, username 중복, 로그인, JWT, 만료, user_id 위조 방지, 로그아웃, 권한

### F. 하우징
- `06_housing/F-01_to_F-10_detailed.md` : 하우스 조회, 가구 소유권, 배치 수량, 이동/회전/삭제, 벽지·바닥, 다른 집 방문

### G. 상점
- `07_shop/G-01_to_G-10_detailed.md` : 상품 조회, 구매 모달, Atomic Update, 잔액 부족, 연타, Inventory upsert, rollback

### H. 출석
- `08_attendance/H-01_to_H-10_detailed.md` : 첫 출석, 연속 출석, 중복 요청, UNIQUE, 보상 transaction, 자정/timezone

## 작성 원칙

- 확정된 요구사항과 아직 미정인 규칙을 섞지 않는다.
- 가격, 확률, 점수, 제한시간처럼 기획에서 결정해야 하는 숫자는 임의로 확정하지 않는다.
- 단순 조회 시나리오는 간단하게, 재화·Docker·Lock·Transaction·WebSocket처럼 위험한 부분은 더 자세히 적는다.
- 프론트 버튼 비활성화는 UX 방어이고, 실제 어뷰징 방지는 반드시 백엔드/DB에서도 처리한다.
- 재화 변경은 가능한 경우 DB Atomic Update를 사용한다.
- 여러 상태를 함께 확인해야 하는 세션 변경은 필요한 구간에서만 `SELECT ... FOR UPDATE`를 검토한다.
- 하루 한 번처럼 유일성 자체가 규칙이면 DB UNIQUE 제약을 우선 활용한다.
- 시나리오가 확정되기 전에는 코드에 미정 규칙을 임의로 넣지 않는다.

> 현재는 설계·학습용 임시 문서입니다. 이후 팀에서 규칙을 확정하면 이 문서들을 API 명세와 테스트 케이스의 기준으로 사용합니다.
