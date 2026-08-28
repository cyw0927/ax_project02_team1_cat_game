# 03. 제출

## 목적
사용자가 작성한 코드를 서버에 전달하고, 채점 가능한 attempt를 안전하게 생성하는 단계다.

## 정상 흐름
1. 사용자가 제출 버튼 클릭.
2. 서버가 사용자/문제/요청 형식을 검증.
3. TASK 활성 상태 재확인.
4. 제출 코드를 `TASK_ATTEMPTS`에 PENDING으로 저장.
5. 짧은 트랜잭션 commit.
6. attempt_id와 접수 상태를 빠르게 반환.
7. 채점 작업을 Background 실행으로 넘김.

## 변수 A. 제출 버튼 연타
- 원인: 응답 지연, 사용자 반복 클릭.
- 위험: attempt 다중 생성과 보상 중복.
- 해결: 버튼 잠금은 UX 보조일 뿐. 서버에서 중복 제출/보상 정책을 별도로 보호.

## 변수 B. 서버 저장 전 네트워크 단절
- 서버에 attempt가 없을 수 있음.
- 재접속 시 최근 attempt 조회로 실제 접수 여부 확인.

## 변수 C. commit 성공 후 응답 유실
- 서버에는 attempt가 존재.
- 사용자가 다시 제출해 새 attempt가 생길 수 있음.
- 최근 attempt 조회 또는 향후 idempotency 정책 검토.

## 변수 D. 빈 코드/잘못된 타입/과도한 길이
- API 입력 검증에서 거절.
- Docker까지 보내지 않는다.

## 변수 E. 제출 순간 TASK 비활성화
- 서버가 다시 활성 상태 검사.
- 비활성이면 attempt를 정상 채점 대상으로 만들지 않는다.

## 변수 F. 존재하지 않는 user_id/task_id
- 404/계약에 맞는 오류 반환.
- FK 오류까지 보내기 전에 의미 있는 검증 권장.

## 변수 G. DB 저장 실패
- PENDING insert가 commit되지 않았다면 Background 채점을 시작하지 않는다.
- 사용자에게 접수 성공처럼 표시하지 않는다.

## 변수 H. 여러 사용자가 동시에 제출
- 각 attempt는 독립적.
- 동시 제출 수만큼 Docker를 즉시 생성하지 않고 채점 계층에서 실행 수 제한.

## 변수 I. 힌트 사용 상태 누락
- used_hint가 정책에 중요하다면 제출 시 서버가 신뢰 가능한 방식으로 기록해야 한다.
- 현재 힌트 정책은 `TBD`.

## 트랜잭션 원칙

권장:
```text
BEGIN
INSERT TASK_ATTEMPTS(PENDING)
COMMIT
→ HTTP 응답
→ DB 밖에서 Docker 실행
```

금지:
```text
BEGIN
INSERT PENDING
Docker 끝날 때까지 기다림
UPDATE 결과
COMMIT
```

외부 실행 동안 DB transaction/row lock을 잡지 않는다.

## UI
- 접수 전: `제출`
- 접수 성공: `채점 대기 중`
- 요청 실패: `제출에 실패했습니다. 접수 여부를 확인 후 다시 시도해주세요.`

## 다음 단계 조건
- attempt 생성 성공 → `04_grading.md`
- 입력 검증 실패 → 코드 작성 화면
- DB/서버 실패 → 재시도 또는 최근 attempt 확인

## 테스트 케이스
- 정상 제출
- 더블클릭
- 빈 코드
- 매우 큰 코드
- 잘못된 user/task
- 비활성 TASK
- insert 전 네트워크 단절
- commit 후 응답 유실
- DB 오류
- 동시 다수 제출

## TBD
- 제출 idempotency key 도입 여부
- 코드 크기 제한
- 중복 attempt 허용 정책
