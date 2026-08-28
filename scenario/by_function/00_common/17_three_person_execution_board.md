# 백엔드 3명 분업 실행표

목표는 세 명이 같은 파일을 동시에 만지는 일을 줄이고, 공통 규칙을 먼저 맞춘 뒤 병렬로 개발하는 것이다.

## 담당 A - 학습/채점/Sandbox

주 폴더:
```text
server/app/learning/
server/app/sandbox/
```

우선 작업:
1. TASKS 상세 조회 계약 확정
2. 문제 제출 PENDING 생성
3. BackgroundTasks 연결
4. Docker 동시 실행 제한
5. test_cases 형식 확정 및 채점 연결
6. PASSED/WRONG_ANSWER/RUNTIME_ERROR/TIMEOUT/SYSTEM_ERROR 처리
7. 최초 정답 보상 중복 방어
8. polling 결과 조회 검증

완료 전 필수 테스트:
- 정상/오답/오류/무한루프
- Docker 옵션
- 동시 제출
- 최초 정답 중복 보상

## 담당 B - 가챠/경제/하우징/출석

주 폴더:
```text
server/app/cats/
server/app/economy/
server/app/housing/
server/app/users/ (출석 구간)
```

우선 작업:
1. 가챠 가격/확률/중복 정책 확정 대기
2. 가챠 transaction 구현
3. 상점 기존 Atomic Update 검증
4. Inventory upsert 검증
5. 출석 UNIQUE + 보상 transaction 검증
6. 하우징 배치 수량 race condition 검토
7. position_data 스키마/범위 확정 후 검증 추가
8. 벽지/바닥 category 및 소유권 테스트

완료 전 필수 테스트:
- 구매/가챠 연타
- rollback
- 출석 50건 동시 요청
- 미보유 가구 배치
- 보유량 초과 배치

## 담당 C - 배틀/승급전/인증

주 폴더:
```text
server/app/battle/
server/app/ranking/
server/app/users/ 또는 신규 auth 영역
```

우선 작업:
1. 방 시작 최소 인원/Ready/방장 참가 규칙 확정
2. 방 입장 FOR UPDATE 검증
3. 배틀 점수 정책 확정
4. WebSocket 연결/score_update
5. 종료/승자 계산/보상 transaction
6. 승급전 문제 수/제한시간/합격조건 확정
7. 승급전 제출/채점/완료 처리
8. JWT 인증 구현
9. 기존 user_id body/path를 인증 사용자 기준으로 단계적 전환

완료 전 필수 테스트:
- 마지막 자리 동시 입장
- 일반 참가자의 시작 요청
- WebSocket 재접속
- 만료된 승급전 제출
- 다른 사용자 자원 변경 시도

## 세 명이 같이 먼저 결정할 것

개별 개발 전에 아래는 공동 확정한다.

```text
1. TASK_ATTEMPTS 상태값
2. test_cases 저장 형식
3. 학습 정답 보상/힌트 정책
4. 가챠 가격/확률/중복/천장
5. 배틀 점수/종료/승자/보상
6. 승급전 문제 수/제한시간/합격/점수
7. 인증 방식/JWT 만료
8. 방 시작 최소 인원/Ready 조건
9. 재화 종류와 컬럼 의미
10. timezone 기준
```

## Git branch 예시

```text
feature/learning-grading
feature/gacha-economy-housing
feature/battle-ranking-auth
```

DB 모델 변경이 들어가면 해당 변경을 먼저 공유한다. 세 명이 동시에 서로 다른 Alembic migration을 만들어 충돌시키지 않는 것이 중요하다.

## 작업 흐름

```text
시나리오 확인
→ 미정 규칙 질문/확정
→ API 계약 고정
→ branch
→ 구현
→ 정상 테스트
→ 예외 테스트
→ 동시성 테스트(필요 시)
→ Swagger 확인
→ PR
→ 다른 담당자 review
→ merge
```

## 리뷰 시 질문

리뷰어는 코드 스타일보다 먼저 다음을 본다.

- 프론트 값을 그대로 믿고 있지 않은가?
- transaction 중간에 실패하면 데이터가 반쯤 저장되지 않는가?
- 재화/보상 중복이 가능한가?
- 상태가 이미 바뀐 뒤에도 요청이 성공하는가?
- 없는 자원/다른 사용자의 자원 접근을 막는가?
- 미정 규칙을 개발자가 임의로 숫자로 넣지 않았는가?

이 실행표는 담당자가 바뀌어도 기능 소유권과 검증 범위를 빠르게 파악하기 위한 임시 기준이다.
