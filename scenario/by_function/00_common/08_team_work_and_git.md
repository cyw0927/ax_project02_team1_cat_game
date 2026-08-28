# 3인 분업과 Git 작업 방식

현재 백엔드 기능을 3명이 동시에 진행할 때 같은 파일을 여러 사람이 계속 수정하면 충돌이 커진다. 그래서 가능한 한 도메인 소유권을 나눠 작업한다.

## 추천 역할

### 담당 A

```text
learning/
sandbox/
```

주요 작업:
- 문제 상세 조회
- TaskAttempt 생성
- PENDING/RUNNING 상태
- Docker 채점
- 정답/오답/오류 처리
- 최초 정답 보상 연결

### 담당 B

```text
cats/
economy/
housing/
```

주요 작업:
- 가챠
- 재화 차감
- 상점 기존 흐름 검증
- 출석 기존 흐름 검증(사용자 도메인과 협의)
- 하우징 기존 쓰기 기능 검증

### 담당 C

```text
battle/
ranking/
users/
auth 관련 공통 코드
```

주요 작업:
- 방 시작 규칙
- 실시간 점수
- WebSocket
- 승급전 완료/점수
- 로그인/JWT

## 작업 시작 전 공동 회의

셋이 갈라지기 전에 최소한 다음을 같이 결정한다.

```text
TaskAttempt 상태값
정답 보상 규칙
가챠 가격/확률/중복
배틀 점수/시작/종료
승급전 합격 기준
인증 방식
timezone
```

도메인을 가로지르는 규칙을 각자 다르게 가정하지 않기 위해서다.

## Branch 예시

```text
feature/learning-grading
feature/gacha-economy
feature/battle-ranking-auth
```

기능이 커지면 더 작게 나눠도 된다.

```text
feature/battle-websocket
feature/rank-challenge-complete
```

## 기본 작업 순서

```text
main 최신화
→ branch 생성
→ 작은 기능 구현
→ 직접 실행
→ 정상 테스트
→ 예외 테스트
→ 필요한 동시성 테스트
→ commit
→ push
→ PR
→ 다른 팀원이 review
→ 수정
→ merge
```

## DB 모델 변경 주의

여러 사람이 동시에 model과 Alembic migration을 만들면 충돌하기 쉽다.

따라서 DB 컬럼/제약 추가가 필요하면:

1. 팀에 먼저 공유
2. 누가 migration을 만들지 한 명 정함
3. 해당 PR을 먼저 merge
4. 나머지 팀원이 최신 main을 pull/rebase
5. 이후 기능 작업 계속

## 다른 도메인 코드를 직접 수정해야 할 때

예를 들어 A가 정답 보상을 넣으면서 `USERS.balance`를 건드려야 할 수 있다.

이때 economy 전체 구조를 임의로 바꾸지 말고 필요한 인터페이스/규칙을 B와 확인한다.

즉 '내 폴더만 수정'이 절대 규칙은 아니지만, 소유 도메인의 규칙을 바꾸는 작업은 담당자와 공유한다.

## PR 크기

한 PR에 학습+가챠+배틀을 모두 넣지 않는다.

좋은 예:

```text
feat: add task attempt grading worker
fix: prevent duplicate room participants
test: add attendance duplicate check
```

리뷰어가 무엇이 바뀌었는지 설명할 수 있을 정도로 나눈다.

## 충돌을 줄이는 핵심

```text
main.py 같은 공통 파일은 최소 수정
도메인별 router/models에 기능 배치
migration 담당 순서 정하기
미정 규칙을 각자 코드에 먼저 넣지 않기
```

최종 목표는 '누가 많이 코딩했는가'가 아니라 각 팀원이 자신이 맡은 API의 흐름과 방어 이유를 설명할 수 있는 상태다.