# 01. 학습 문제 제출·채점

이 폴더는 사용자가 학습 문제를 선택하고 코드를 작성한 뒤 제출하여 채점 결과를 받기까지의 전체 흐름을 설명합니다.

주요 내용은 다음과 같습니다.

- 문제 목록/상세 조회
- 활성 문제 여부 확인
- 코드 제출
- `TASK_ATTEMPTS`의 `PENDING` 상태 저장
- BackgroundTasks 기반 비동기 처리 방향
- Docker SDK를 이용한 격리 채점
- Docker 동시 실행 제한
- 정답, 오답, 실행 오류, 시간 초과, 시스템 오류 구분
- 재제출과 최초 정답 보상 중복 방어
- Polling을 이용한 채점 결과 조회

주요 테이블: `CONCEPTS`, `TASKS`, `USER_PROFICIENCY`, `TASK_ATTEMPTS`, `USERS`

주요 기술 영역: FastAPI, PostgreSQL, Docker SDK for Python, BackgroundTasks, 동시 실행 제한
