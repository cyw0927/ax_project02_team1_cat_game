# Docker 채점 아키텍처 정리

이 문서는 사용자 Python 코드를 FastAPI 서버에서 안전하게 채점하기 위한 공통 설계 초안이다.

## 1. 실행 방식

터미널에서 직접 `docker run`을 입력하는 방식이 아니라 FastAPI Python 코드가 **Docker SDK for Python(`docker` 패키지)** 을 통해 Docker Engine을 제어한다.

```text
사용자 코드 제출
→ TASK_ATTEMPTS에 PENDING 저장
→ 백그라운드 채점 함수
→ Docker SDK
→ 채점용 이미지로 컨테이너 생성
→ 테스트 실행
→ stdout/stderr/종료코드 수집
→ 결과 저장
→ 컨테이너 제거
```

## 2. 필수 자원 제한

채점 컨테이너에는 최소한 다음 제한이 필요하다.

```text
메모리: 128MB
CPU: 0.5
네트워크: 완전 차단
파일시스템: read-only
```

추가 hardening으로 다음도 유지할 수 있다.

- capability drop
- no-new-privileges
- stdin/tty 비활성화
- 출력 크기 제한
- 실행시간 제한
- 실행 후 컨테이너 cleanup

## 3. 왜 네트워크를 막나

사용자 제출 코드는 신뢰할 수 없다. `requests`, socket 등을 이용해 외부 네트워크에 접속하거나 데이터를 내려받으려 할 수 있으므로 채점에는 인터넷이 필요하지 않다는 전제에서 network를 차단한다.

## 4. 왜 read-only인가

사용자가 파일을 마음대로 만들거나 시스템 파일을 변경하는 것을 줄이기 위해 컨테이너 기본 파일시스템을 읽기 전용으로 둔다. 만약 Python 실행 자체에 임시 쓰기 공간이 꼭 필요하면 최소 범위의 tmpfs 등을 별도로 검토해야 한다.

## 5. 동시 실행 제한

FastAPI가 30개 요청을 받을 수 있다고 Docker 30개를 동시에 만들면 안 된다.

```text
30 attempts PENDING
↓
실행 슬롯 최대 3~5개
↓
끝난 만큼 다음 attempt 실행
```

정확한 동시 실행 개수는 설정값으로 두는 것이 좋다.

### MVP 주의

`threading.BoundedSemaphore`는 한 Python 프로세스 기준이다. Uvicorn worker를 여러 개 띄우면 전체 서버의 컨테이너 수 제한이 깨질 수 있다.

교육용 MVP에서는 단일 worker 전제를 문서로 남기고, 규모 확장 시 Redis/Celery 등의 외부 queue/coordination을 검토한다.

## 6. 상태 흐름

추천 초안:

```text
PENDING
→ RUNNING
→ PASSED
   WRONG_ANSWER
   RUNTIME_ERROR
   TIMEOUT
   SYSTEM_ERROR
```

이 상태값은 아직 팀 최종 확정 전이라면 코드와 프론트에 박기 전에 승인한다.

## 7. 사용자 코드 오류와 시스템 오류 구분

- 테스트 결과 다름 → `WRONG_ANSWER`
- Python 실행 중 예외 → `RUNTIME_ERROR`
- 제한시간 초과 → `TIMEOUT`
- Docker Engine/이미지/서버 문제 → `SYSTEM_ERROR`

사용자가 고칠 수 있는 문제와 서버 운영자가 고쳐야 하는 문제를 섞지 않는다.

## 8. BackgroundTasks의 한계

FastAPI `BackgroundTasks`는 간단하고 MVP에 적합하지만 영속적인 queue가 아니다.

```text
PENDING 저장
→ background task 등록
→ 서버 프로세스 강제 종료
```

되면 DB에는 PENDING만 남고 작업은 사라질 수 있다.

따라서 최소한 다음 정책을 논의해야 한다.

- 일정 시간 이상 PENDING인 작업을 어떻게 정리할지
- 서버 재시작 후 복구할지
- 사용자가 다시 제출하게 할지

## 9. 테스트해야 하는 것

- 정상 코드
- 오답 코드
- SyntaxError/NameError 등
- 무한루프
- 메모리 과다 사용 코드
- 외부 네트워크 접속 코드
- 파일 쓰기 시도
- 동시에 다수 제출
- Docker unavailable 상황
- 모든 경우 컨테이너가 cleanup되는지

## 10. 중요한 원칙

채점 컨테이너는 '사용자에게 실행 환경을 제공하는 서버'가 아니라 **일회용 검사 상자**다. 필요한 입력만 넣고 결과만 받고 바로 버리는 구조로 유지한다.