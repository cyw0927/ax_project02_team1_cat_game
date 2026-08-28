# 03. 승급전 생성 및 문제 구성

## 목적
하나의 승급전 도전을 서버에서 생성하고, 해당 도전에 사용할 문제와 제한 시간을 고정하는 단계다.

## 정상 흐름
1. 서버가 도전 가능 상태를 다시 확인한다.
2. RANK_CHALLENGES를 생성한다.
3. 문제 선정 규칙에 따라 문제 목록을 확정한다.
4. RANK_CHALLENGE_TASKS에 task_order와 함께 저장한다.
5. started_at, expires_at을 서버 기준으로 기록한다.
6. challenge_id와 문제 목록을 반환한다.

## 발생 가능한 변수
### A. 문제 선정 중 비활성 TASK 포함
- 원인: 선정 직전 문제 비활성화, 오래된 캐시.
- 해결: challenge 생성 시 `is_active`를 재확인하고 사용할 수 없는 문제는 제외한다. 대체 문제 규칙은 `TBD`.

### B. 동일 TASK 중복 선정
- 위험: 같은 문제를 두 번 풀게 됨.
- 해결: `(challenge_id, task_id)` UNIQUE 원칙 활용.

### C. task_order 중복
- 해결: `(challenge_id, task_order)` UNIQUE 원칙 활용.

### D. challenge만 생성되고 문제 저장 실패
- 원인: DB 오류.
- 해결: challenge 생성과 문제 매핑 저장은 하나의 짧은 트랜잭션으로 처리해 불완전 challenge를 남기지 않는다.

### E. expires_at을 클라이언트가 조작
- 해결: 제한 시간은 서버가 계산하고 권위 상태로 저장한다. 클라이언트 타이머는 표시용.

### F. 문제 개수/선정 난이도 규칙 미확정
- 정책: `TBD`. 현재 문서에서 숫자나 난이도 비율을 임의 확정하지 않는다.

## DB/API 영향
- RANK_CHALLENGES
- RANK_CHALLENGE_TASKS
- TASKS

## 다음 단계 조건
- challenge와 문제 목록 저장 성공 → `04_solve_save.md`
- 문제 구성 실패 → 전체 rollback 후 재시도/오류 안내

## 테스트
- 정상 생성
- 중복 task
- 중복 order
- 비활성 task
- 문제 저장 중 DB 오류
- 두 요청 동시 생성
- 서버 기준 시간 기록
