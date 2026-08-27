# 01. 학습 문제 제출·채점

사용자가 문제를 열고 코드를 제출한 뒤 비동기 채점 결과와 보상까지 받는 흐름을 정리한 폴더입니다.

## 문서 읽는 순서

1. `A-01_task_detail_view.md` : 문제 하나를 여는 흐름
2. `A-02_to_A-10_detailed.md` : 제출·PENDING·채점·오류·재제출·보상 시나리오
3. `API_SPEC_DRAFT.md` : 실제 Endpoint / Request / Response / 상태코드
4. `DB_BEFORE_AFTER.md` : 제출·채점·보상 전후 DB 변화
5. `TEST_CASES.md` : `NOW / AFTER / POLICY` 테스트 목록

## 현재 main 구현 상태

```text
GET /concepts                    DONE
GET /tasks                       DONE
POST /attempts                   DONE — PENDING 저장 + 202
GET /attempts/{attempt_id}       PARTIAL — polling API는 있으나 실제 채점 미연결
Docker Sandbox executor          DONE — learning과 미연결
BackgroundTask → Docker 채점     MISSING
정답 보상/숙련도 갱신             MISSING/POLICY
```

## 핵심 기준

- 일반 사용자 Response에 `TASKS.test_cases`를 노출하지 않습니다.
- 제출 요청은 Docker 실행 완료까지 기다리지 않고 먼저 `PENDING`을 저장하고 `202 Accepted`를 반환하는 방향입니다.
- Docker 제한은 memory 128MB / CPU 0.5 / network none / read-only입니다.
- 여러 제출이 동시에 와도 실제 컨테이너 실행 수를 제한합니다.
- 정답 보상은 중복 지급되지 않도록 서버/DB에서 방어해야 합니다.

주요 테이블: `CONCEPTS`, `TASKS`, `USER_PROFICIENCY`, `TASK_ATTEMPTS`, `USERS`

아직 확정하지 않은 값: 최종 status 목록, test_cases 형식, timeout/output cap, 보상 공식, 힌트 보상, 숙련도 공식.
