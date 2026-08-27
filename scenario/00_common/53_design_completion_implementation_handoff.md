# 문서 설계 완료 · 구현 인수인계

이 문서는 지금까지 작성한 시나리오 설계를 **여기서 종료하고 실제 구현 단계로 넘기기 위한 최종 인수인계 문서**다.

핵심 판정:

```text
문서 구조/설계 = 완료
비즈니스 미정사항 = 존재
실제 코드 구현 = 진행 필요
```

`비즈니스 규칙이 아직 미정`이라는 것은 문서 설계가 덜 끝났다는 뜻이 아니다.

오히려 임의로 숫자와 정책을 확정하지 않고 **어디가 미정인지 명확히 기록한 상태**를 설계 완료 상태로 본다.

---

# 1. 문서 설계 완료 범위

A~H 8개 도메인에 다음 세트가 준비되어 있다.

```text
도메인 README
상세 시나리오 10개
API_SPEC_DRAFT.md
DB_BEFORE_AFTER.md
TEST_CASES.md
```

대상:

```text
A 학습·채점
B 가챠·고양이
C 실시간 배틀
D 랭킹·승급전
E 인증·JWT
F 하우징
G 상점
H 출석
```

공통 설계에는 다음 범위가 정리되어 있다.

```text
API 계약
HTTP 오류
DB transaction/concurrency
Docker sandbox
polling/WebSocket
테스트
Git 협업
migration
도메인 데이터 흐름
구현 순서
Definition of Done
제품 흐름
API inventory
DB Before/After
실패 케이스
상태 전이
보상/재화 write
권한
시간/timezone
idempotency
logging
환경변수
validation
복구
WebSocket 계약
BackgroundTask
보안/abuse
성능/index
E2E
현재 코드 감사
schema gap
API gap
migration 계획
release gate
```

따라서 요구사항이 새로 바뀌지 않는 한 **설계를 더 잘게 쪼개는 새 문서를 계속 추가할 필요는 없다.**

---

# 2. 문서 우선순위

문서끼리 표현이 충돌하면 다음 순서로 본다.

```text
1. 실제로 확정된 사용자/팀 요구사항
2. 13_latest_product_flow.md
3. 01_business_rule_decision_checklist.md
4. 각 도메인 API_SPEC_DRAFT.md
5. 각 도메인 DB_BEFORE_AFTER.md
6. 각 도메인 TEST_CASES.md
7. 48_current_backend_implementation_status.md
8. 50_api_implementation_gap_matrix.md
9. 오래된 상세 예시/추천안
```

오래된 문서의 예시 숫자가 최신 확정사항보다 우선하지 않는다.

기획이 변경되면 새 파일을 무조건 만들기보다 **관련 기존 문서를 같이 수정**한다.

---

# 3. 현재 확정된 핵심 기준

## 제품 흐름

```text
로그인
→ 홈
→ 학습 / 배틀 / 승급전
→ 결과/보상
→ 재화
→ 상점 / 가챠
→ 가구 / 고양이
→ 하우징
```

## 출석

```text
매일 자정 이후 첫 로그인
→ 자동 출석 1회
→ 100원 지급
```

- 같은 날 재로그인에서 추가 지급 없음
- 로그인 자체는 정상 성공
- `(user_id, check_in_date)` UNIQUE가 최종 방어선
- 출석 INSERT와 보상 지급은 같은 transaction
- 날짜는 서버가 결정
- 서비스 timezone의 실제 값은 아직 팀 결정사항

## Docker 채점

확정된 안전 조건:

```text
memory = 128MB
CPU = 0.5
network = none
filesystem = read-only
```

구조:

```text
POST /attempts
→ PENDING commit
→ 202 Accepted
→ BackgroundTask
→ 제한된 수의 Docker 실행
→ 최종 상태 저장
→ polling
```

정확한 timeout/output cap/최종 status set은 아직 결정 대상이다.

## DB 동시성

```text
단순 재화 차감
→ Atomic conditional UPDATE

여러 상태를 함께 일관되게 검사
→ 필요한 구간 SELECT ... FOR UPDATE

하루 한 번/조합 유일성
→ DB UNIQUE
```

프론트 버튼 비활성화는 최종 데이터 방어가 아니다.

## 실시간 배틀

```text
DB commit
→ WebSocket broadcast
```

WebSocket connection memory가 게임 상태의 최종 저장소가 아니다.

재접속은 DB snapshot으로 복구한다.

## 인증 방향

현재는 일부 API가 path/body `user_id`를 받지만 최종 방향은:

```text
JWT
→ current_user
→ 서버가 사용자 식별
```

이다.

---

# 4. 설계는 끝났지만 반드시 결정해야 하는 P0

다음은 **문서가 부족해서 남은 일이 아니라 실제 비즈니스/데이터 결정**이다.

## 학습

- `TASKS.test_cases` 실제 형식
- 최종 `TASK_ATTEMPTS.status` 목록
- 결과 메시지 저장 여부
- 정답 보상 조건/중복 지급 기준
- 힌트와 보상 관계

## 경제·가챠

- 최종 재화 구조
- 가챠 1회 비용
- 실제 확률/희귀도
- 중복 고양이 처리
- mileage/티켓 사용 방식

천장은 MVP 이후로 미룰 수 있다.

## 배틀

- 시작 조건
- 점수 공식
- 오답/재도전
- 사용자-방-문제별 중복 득점 저장 구조
- 종료 조건
- 결과/보상 1회 지급 구조

특히 중복 득점 저장 구조가 정해지기 전 scoring을 완료 처리하지 않는다.

## 승급전

- 문제 수
- 제한시간
- 합격 기준
- 오답 재도전
- SUCCESS/FAILED 점수 변화
- 성공 보상

## 인증

- 로컬 username/password인지 다른 방식인지
- password_hash/username UNIQUE 등 USERS schema
- access/refresh 정책

## 하우징/고양이

- 고양이를 직접 좌표에 배치하는지 자동으로 움직이는지
- 직접 배치라면 USER_CATS 위치 저장 방식

---

# 5. P1 — 구현하면서 결정 가능한 것

다음은 핵심 구조를 막지는 않지만 해당 기능 완성 전에 필요하다.

- 문제 `title/description` 저장 여부
- Docker timeout
- Docker output cap
- 하우징 x/y/rotation schema
- 좌표 범위/겹침 정책
- 판매중지 `ITEMS.is_active` 필요 여부
- `CATS` 가챠 활성상태 필요 여부
- 서비스 timezone 실제 값
- 로그인 Response에 자동 출석 결과 포함 여부
- saved_code 복원 API 모양

---

# 6. 지금 바로 코딩/테스트 가능한 영역

기획 숫자를 새로 만들지 않고도 진행 가능한 작업이다.

## 기존 기능 자동 테스트

```text
상점 구매
출석 수동 transaction
하우징 기본 CRUD
배틀 lobby/join/Ready/ROOM_TASKS
승급전 생성/코드 저장
학습 조회/PENDING 접수
```

먼저 `TEST_CASES.md`의 **NOW** 항목을 코드 테스트로 옮길 수 있다.

## 기술적 보완

정책을 새로 만들지 않는 범위에서:

- 하우징 수량 초과 동시 배치 race 방어
- DB rollback 테스트
- 기존 API Response에 숨겨야 할 필드 보안 테스트
- 현재 Docker executor 단위 테스트
- config/.env validation
- migration clean DB 검증

을 진행할 수 있다.

---

# 7. 작은 결정 후 바로 들어갈 수 있는 영역

## 학습 실제 채점

최소 다음 3개가 정해지면 구현 속도가 빨라진다.

```text
test_cases 형식
status 목록
timeout/output cap
```

그 다음:

```text
POST /attempts
→ BackgroundTask
→ Sandbox
→ final status
```

을 먼저 완성하고 보상은 뒤에 붙일 수 있다.

## 인증

로그인 방식을 한 번 정하면:

```text
USERS migration
→ auth router
→ JWT dependency
→ /me
→ 자동 출석 연결
→ 기존 user_id 제거
```

순서로 진행한다.

---

# 8. 기획 결정 전 구현을 보류해야 하는 영역

다음은 임시 숫자를 넣고 시작하면 되돌리는 비용이 크다.

```text
가챠 실제 pull write
배틀 scoring
배틀 결과 reward
승급전 최종 성공/실패 reward
재화 2종 이상 schema 변경
고양이 하우징 배치 schema
```

이 영역은 관련 P0 결정 후 migration/API/코드를 같이 맞춘다.

---

# 9. 3인 백엔드 개발 착수안

기존 3인 실행 보드의 추천 분할을 유지한다.

## 담당 A — learning / sandbox

```text
학습 NOW 테스트
BackgroundTask 연결
sandbox grading harness
최종 attempt 상태
polling
학습 보상 중복 방어
```

## 담당 B — users / economy / cats / housing

```text
출석 테스트/공통 service
상점 transaction 테스트
하우징 race 보완
가챠 정책 확정 후 write
고양이 ownership/memory
```

## 담당 C — auth / battle / ranking

```text
인증 결정 후 JWT
배틀 lobby 테스트
WebSocket
scoring 구조 확정 후 점수
승급전 채점/상태전이
```

이 분할은 강제가 아니라 **migration/파일 충돌을 줄이기 위한 추천**이다.

공유 모델인 `USERS`, `TASKS`, `TASK_ATTEMPTS`를 변경할 때는 반드시 서로 먼저 알린다.

---

# 10. 추천 구현 순서

```text
0. P0 중 당장 필요한 규칙 짧게 확정
1. 현재 DONE/PARTIAL API 자동 테스트
2. 학습 BackgroundTask + Docker 실제 채점
3. 인증/JWT + 첫 로그인 자동 출석
4. 경제 최종 구조 확정
5. 가챠 write + USER_CATS
6. 하우징/고양이 연결
7. 배틀 scoring 데이터 구조 + 채점
8. WebSocket + 재접속
9. 배틀 결과/보상
10. 승급전 채점/상태/보상
11. E2E
12. release gate
```

단, 팀원들이 병렬 개발하면 서로 독립적인 단계는 동시에 진행할 수 있다.

---

# 11. PR 단위

한 PR에 프로젝트 전체를 넣지 않는다.

좋은 예:

```text
test: cover current shop purchase concurrency
feat: connect learning attempts to background grading
feat: add auth and current user dependency
feat: add automatic attendance on first login
feat: add gacha transaction
feat: add battle websocket events
```

migration이 필요한 PR은 어떤 model을 바꾸는지 제목/본문에 명확히 쓴다.

---

# 12. 문서 변경 규칙 — 이제부터

이 시점부터 요구사항이 그대로라면 **새 설계 문서를 계속 추가하지 않는다.**

구현하면서 발견한 차이는:

```text
현재 코드가 바뀜
→ 48_current_backend_implementation_status 갱신
→ 50_api_implementation_gap_matrix 갱신
→ 해당 도메인 README/API/DB/TEST 갱신
```

비즈니스 규칙이 확정되면:

```text
01_business_rule_decision_checklist 체크
→ 관련 API_SPEC_DRAFT 수정
→ DB/migration 필요성 확인
→ TEST_CASES 기대값 확정
```

제품 흐름 자체가 바뀌면 먼저:

```text
13_latest_product_flow.md
→ 10_cross_domain_data_flow.md
```

를 수정한다.

---

# 13. 구현 완료 판정

세 단계로 구분한다.

```text
IMPLEMENTED
= 코드 존재

TESTED
= 정상/실패/DB 변화/rollback 검증

RELEASE_READY
= E2E + 동시성 + 권한 + 보안 + 장애복구까지 핵심 위험 통과
```

최종 release 판단은 `52_mvp_backend_release_gate.md`를 사용한다.

---

# 14. 최종 결론

현재 시점에서 **문서 설계 작업은 완료**로 본다.

남은 것은 두 종류다.

```text
1. 팀/기획이 선택해야 하는 실제 비즈니스 규칙
2. 그 결정과 문서를 기준으로 하는 코드 구현/테스트
```

따라서 다음 단계는 더 많은 설계 파일 작성이 아니라:

```text
미정 P0 필요한 만큼 확정
→ 구현
→ 테스트
→ 기존 문서 상태 갱신
```

이다.

**새 요구사항이 생기기 전까지 이 문서를 설계 단계의 마지막 인수인계 문서로 사용한다.**