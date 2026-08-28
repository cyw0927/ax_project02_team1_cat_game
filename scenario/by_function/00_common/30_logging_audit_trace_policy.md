# 로그·감사 추적 정책

이 문서는 문제가 발생했을 때 **누가 어떤 요청을 했고 어디서 실패했는지 추적할 수 있도록 어떤 정보를 남길지** 정리한다.

로그는 모든 데이터를 무조건 저장하는 것이 아니라, 장애 분석과 보안에 필요한 정보만 남긴다.

---

## 1. 왜 필요한가

예:

```text
사용자: 코인이 줄었는데 아이템이 없어요
```

이때 서버가 확인할 수 있어야 한다.

```text
구매 요청이 들어왔는가?
어떤 user/item이었는가?
Atomic Update는 성공했는가?
Inventory 단계에서 실패했는가?
최종 COMMIT/ROLLBACK은 무엇이었는가?
```

---

## 2. 기본 로그 항목

요청 단위로 가능하면 다음을 남긴다.

```text
request_id
HTTP method
path
status code
처리 시간
로그인 user_id(가능한 경우)
주요 resource id
오류 종류
```

비밀번호, JWT 원문, DB 비밀번호 같은 값은 남기지 않는다.

---

## 3. 도메인별 중요 로그

### 학습/채점

```text
attempt_id
task_id
PENDING/RUNNING/최종상태
Docker 시작/종료
TIMEOUT/SYSTEM_ERROR
```

사용자 전체 submitted_code를 일반 로그에 그대로 복제할 필요는 없다. 이미 DB에 저장되는 구조라면 ID로 추적한다.

### 상점

```text
user_id
item_id
구매 성공/실패
INSUFFICIENT_BALANCE 여부
최종 quantity
```

재화의 정확한 변경액을 감사 목적으로 남길지는 정책을 정한다.

### 가챠

```text
user_id
pull request id
비용 차감 성공 여부
선택된 cat_id
중복 처리 결과
transaction commit/rollback
```

확률 난수 원시값까지 일반 로그로 남길 필요는 없지만, 공정성 검증 요구가 생기면 별도 검토.

### 배틀

```text
room_id
user_id
join/ready/start/finish
score update
WebSocket connect/disconnect
```

### 승급전

```text
challenge_id
start
code save
TIMEOUT
SUCCESS/FAILED
```

### 출석

```text
user_id
check_in_date
성공/중복
```

---

## 4. 로그 레벨

```text
INFO    정상적인 주요 이벤트
WARNING 예상 가능한 비정상/주의 상황
ERROR   요청 실패/DB/Docker 오류
DEBUG   개발 중 상세 정보
```

운영에서 DEBUG를 과도하게 켜면 로그가 너무 많아지고 민감정보가 섞일 수 있다.

---

## 5. 사용자에게 보여줄 오류와 서버 로그 분리

사용자 Response:

```json
{"detail": "Grading system error"}
```

서버 로그:

```text
DockerException: image not found ...
attempt_id=...
```

사용자에게 traceback 전체를 보내지 않는다.

---

## 6. 감사 데이터와 애플리케이션 로그의 차이

TASK_ATTEMPTS, RANK_CHALLENGES 같은 DB 데이터는 서비스 이력 그 자체다.

로그는 운영 추적 도구다.

```text
DB 기록 = 사용자가 실제로 수행한 상태/이력
서버 로그 = 그 처리가 어떻게 진행됐는지 기술적 흔적
```

둘을 같은 것으로 생각하지 않는다.

---

## 7. request_id

한 요청을 여러 함수/로그에서 추적하려면 request_id가 유용하다.

예:

```text
request_id=abc
→ API 진입
→ DB update
→ Docker 호출
→ 결과 저장
```

FastAPI middleware로 생성하는 방식을 검토할 수 있다.

---

## 8. 로그에 남기면 안 되는 것

- password 평문
- password_hash를 불필요하게 출력
- JWT 전체 토큰
- DATABASE_URL 비밀번호
- API key
- `.env` 전체 내용
- 사용자 코드 전체를 반복적으로 로그에 출력
- 숨겨진 test_cases 전체를 일반 응답/로그로 노출

---

## 9. 테스트

- Docker SYSTEM_ERROR 발생 시 attempt_id로 추적 가능
- 상점 rollback 발생 시 실패 위치 확인 가능
- 없는 room 요청 시 404와 resource id 로그 확인
- 500 오류가 사용자에게 traceback을 노출하지 않는지
- 비밀번호/토큰이 로그에 남지 않는지

---

# 결론

좋은 로그는 많이 찍는 로그가 아니라 **문제가 났을 때 원인을 찾을 수 있고 민감정보는 노출하지 않는 로그**다.

MVP에서는 request_id + user/resource id + 상태 변화 + ERROR stack trace 정도를 우선한다.