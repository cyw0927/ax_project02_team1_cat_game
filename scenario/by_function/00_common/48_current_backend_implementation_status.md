# 현재 백엔드 구현 현황 감사

이 문서는 **현재 `main` 브랜치의 실제 코드**와 지금까지 작성한 시나리오 문서를 대조해, 무엇이 구현됐고 무엇이 아직 비어 있는지 한눈에 보기 위한 문서다.

중요:

- `구현됨` = 현재 코드에 endpoint/로직이 존재한다는 뜻이다.
- `부분 구현` = 기본 골격은 있으나 최신 시나리오를 완성하기 위한 핵심 단계가 남아 있다.
- `미구현` = 문서에는 필요하지만 현재 코드에는 없다.
- 기획 미정 숫자/정책은 이 문서에서 새로 확정하지 않는다.

---

## 1. 앱 공통

현재 `app.main`에는 다음 router가 연결돼 있다.

```text
learning
economy
cats
housing
ranking
battle
users
```

루트 상태 확인용:

```http
GET /
```

도 존재한다.

현재 별도 `auth` router는 없다.

### 상태

- FastAPI 기본 앱: **구현됨**
- 도메인 router 등록: **구현됨**
- JWT 인증 공통 dependency: **미구현**
- WebSocket endpoint/connection manager: **미구현**

---

# 2. 학습·채점

## 현재 구현됨

```text
GET /concepts
GET /tasks
GET /users/{user_id}/proficiency
GET /users/{user_id}/attempts
GET /attempts/{attempt_id}
POST /attempts
```

`GET /tasks`는 활성 문제만 반환하고 `test_cases`를 숨긴다.

`POST /attempts`는:

```text
사용자 존재 확인
→ active TASK 확인
→ TASK_ATTEMPTS(PENDING) 생성
→ commit
→ 202 Accepted
```

까지 구현돼 있다.

## 아직 남음

- 문제 하나 상세 조회 `GET /tasks/{task_id}`
- 사용자 화면용 문제 `title/description` 데이터
- `BackgroundTasks` 등록
- PENDING → RUNNING 전환
- Sandbox 실제 호출
- test_cases 해석/채점기
- PASSED / WRONG_ANSWER / RUNTIME_ERROR / TIMEOUT / SYSTEM_ERROR 확정
- 결과 메시지 저장
- 정답 보상
- 숙련도 갱신
- stale PENDING 복구 코드

### 판정

**부분 구현**

접수 API는 있지만 현재 제출하면 실제 Docker 채점으로 이어지지 않는다.

---

# 3. Docker Sandbox

## 현재 구현됨

Docker SDK 기반 executor가 별도 모듈로 존재한다.

현재 코드에서 확인되는 방어:

```text
network_disabled=True
memory limit
nano_cpus
read_only=True
cap_drop=[ALL]
no-new-privileges
stdin/tty 비활성
실행 timeout
출력 크기 제한
container cleanup
BoundedSemaphore
```

## 아직 남음

- TASK.test_cases와 submitted_code를 합쳐 실제 채점용 code 생성
- learning BackgroundTask와 연결
- SandboxResult를 학습 status로 변환
- 설정값 최종 확정/테스트
- single worker 운영 전제 문서와 실제 실행 설정 일치 확인

### 판정

**기술 실행기 구현됨 / 학습 채점과의 연결은 미구현**

---

# 4. 출석

## 현재 구현됨

```text
GET /users/{user_id}
POST /users/{user_id}/attendance/check-in
GET /users/{user_id}/attendances
```

현재 check-in 로직은:

```text
ATTENDANCES INSERT
→ UNIQUE 충돌 처리
→ USERS.balance + 100
→ 같은 transaction 흐름에서 commit
```

형태다.

## 최신 요구사항과 다른 점

확정 요구사항은:

```text
매일 자정 이후 첫 로그인
→ 자동 출석 처리
→ 100 지급
```

이다.

현재 코드는 **사용자가 명시적으로 check-in endpoint를 호출해야 한다.**

또한 날짜 판정이 현재:

```python
date.today()
```

라서 배포 서버 OS timezone에 따라 서비스 날짜가 달라질 수 있다.

## 남음

- 로그인 성공 흐름과 자동 출석 연결
- 서비스 timezone 확정
- 명시적 timezone으로 check_in_date 계산
- 같은 날 재로그인 시 로그인은 정상 성공하고 출석만 건너뛰는 흐름

### 판정

**출석 transaction은 구현됨 / 최종 트리거와 timezone은 미완성**

---

# 5. 상점·경제

## 현재 구현됨

```text
GET /items
POST /shop/buy
GET /users/{user_id}/inventory
```

구매는:

```text
서버에서 ITEM 가격 조회
→ USERS 조건부 Atomic UPDATE
→ INVENTORIES PostgreSQL upsert
→ commit
```

구조다.

잔액 부족은 409로 처리한다.

### 강점

- 프론트 가격을 신뢰하지 않음
- 잔액 음수 방어
- balance 차감 + inventory 증가 transaction
- 동일 item 재구매 quantity 증가

## 남음

- JWT 기준 사용자 식별
- 판매중지/is_active 정책을 넣을 경우 스키마 확장
- 두 종류 이상의 재화를 실제 채택할 경우 경제 스키마 재설계
- category/filter/pagination 필요 시 확장

### 판정

**현재 단일 balance 기반 상점 핵심은 구현됨**

---

# 6. 가챠·고양이

## 현재 구현됨

```text
GET /cats
GET /users/{user_id}/cats
```

즉 CATS master 조회와 USER_CATS 보유 목록 조회까지만 있다.

## 미구현

- 가챠 실행 endpoint
- 비용 Atomic 차감
- 확률 추첨
- USER_CATS INSERT
- 중복 고양이 처리
- mileage 처리
- 천장
- 가챠 transaction rollback 테스트
- 고양이 상호작용/대화 API
- CAT_MEMORIES 읽기/갱신

### 판정

**조회만 구현 / 가챠 핵심 미구현**

---

# 7. 하우징

## 현재 구현됨

```text
GET /users/{user_id}/house
POST /users/{user_id}/house/objects
PATCH /users/{user_id}/house/objects/{placed_object_id}
DELETE /users/{user_id}/house/objects/{placed_object_id}
PUT /users/{user_id}/house/wallpaper
PUT /users/{user_id}/house/floor
```

현재 서버는:

- 사용자 존재
- Inventory 소유 여부
- wallpaper/floor category
- 소유 quantity보다 더 많이 배치하는지

등을 검사한다.

## 남음

- JWT ownership
- `position_data`의 정확한 x/y/rotation 규칙
- 좌표 범위
- 겹침 정책
- 같은 Inventory item을 동시에 여러 번 배치하는 race 방어
- 고양이를 하우징에 배치하는 상태 저장 방식

### 중요한 현재 갭

최신 흐름에는:

```text
가챠 → 고양이 획득 → 하우징에 배치
```

가 있지만 현재 `PLACED_OBJECTS`는 `item_id`만 저장한다.

`USER_CATS`에도 위치/배치 정보가 없다.

따라서 **고양이 하우징 배치 기능은 현재 ERD만으로 표현 방식이 확정되지 않았다.**

### 판정

**가구 하우징은 상당 부분 구현 / 고양이 배치와 위치 검증은 미완성**

---

# 8. 배틀

## 현재 구현됨

```text
GET /rooms
POST /rooms
POST /rooms/{room_id}/participants
PATCH /rooms/{room_id}/participants/{user_id}/ready
POST /rooms/{room_id}/start
POST /rooms/{room_id}/finish
GET /users/{user_id}/rooms
GET /rooms/{room_id}/participants
POST /rooms/{room_id}/tasks
DELETE /rooms/{room_id}/tasks/{task_id}
GET /rooms/{room_id}/tasks
```

방 입장은 `ROOMS ... FOR UPDATE`를 사용해서 마지막 자리 경쟁을 방어한다.

ROOM_PARTICIPANTS/ROOM_TASKS의 UNIQUE도 활용한다.

## 아직 남음

- 방장 자동 참가 여부
- 최소 인원 / Ready 시작 조건
- Start 시 실제 조건 검사
- 배틀 문제 코드 제출/채점
- 문제별 중복 득점 방어
- `current_score` 증가 로직
- WebSocket
- 재접속 snapshot
- 종료 조건 자동 판정
- 승자/순위 계산
- 결과 보상
- 보상 1회 지급 기록

### 현재 코드상 주의

`start_room`은 현재:

```text
방장인가?
WAITING인가?
```

까지만 확인한 뒤 바로 IN_PROGRESS로 바꾼다.

최소 인원/Ready/ROOM_TASKS 존재 같은 조건은 아직 없다.

### 판정

**Lobby/state 기본 골격 구현 / 실제 게임 scoring·realtime·reward 미구현**

---

# 9. 랭킹·승급전

## 현재 구현됨

```text
GET /ranking-groups
GET /ranking-groups/{group_id}/participants
GET /users/{user_id}/ranking-groups
GET /users/{user_id}/rank-challenges
GET /rank-challenges/{challenge_id}/tasks
POST /ranking-groups/{group_id}/rank-challenges
PUT /rank-challenges/{challenge_id}/tasks/{task_id}/code
```

승급전 시작은 challenge와 challenge task들을 같은 transaction에서 만든다.

active challenge 중복 여부, active task 여부도 검사한다.

## 현재 구조와 향후 시나리오 차이

현재 클라이언트가:

```text
task_ids
expires_at
```

을 보내도록 되어 있다.

기획에서 문제 수/제한시간이 서버 규칙으로 확정된다면 서버가 직접 고르는 구조가 더 적합하다.

## 아직 남음

- 승급전 문제 제출/채점
- `is_passed=true` 처리
- TIMEOUT 상태 확정
- SUCCESS / FAILED 전환
- 합격 기준
- current_rank_score 변경
- 성공 보상
- 실패 정책
- 재처리 시 중복 보상 방어

### 판정

**도전 생성/조회/저장 구현 / 실제 승급 판정 미구현**

---

# 10. 인증

현재 main과 router 구조 기준 별도 회원가입/로그인/JWT endpoint가 없다.

또한 USERS 모델에는 현재:

```text
password_hash
email
refresh token 관련 정보
```

가 없다.

대부분의 API가 body/path의 `user_id`를 신뢰하고 있다.

### 판정

**미구현**

---

# 11. 전체 현황 요약

| 영역 | 현재 상태 |
| --- | --- |
| FastAPI 앱/DB 기본 골격 | 구현됨 |
| 학습 조회·제출 접수 | 부분 구현 |
| Docker executor | 구현됨, 미연결 |
| 출석 DB transaction | 구현됨, 로그인 자동 트리거 미연결 |
| 상점 | 핵심 구현됨 |
| 가챠 | 미구현 |
| 고양이 조회 | 구현됨 |
| 가구 하우징 | 부분 구현 |
| 배틀 Lobby | 부분 구현 |
| 배틀 실시간/scoring/reward | 미구현 |
| 승급전 생성/저장 | 부분 구현 |
| 승급전 채점/성공/보상 | 미구현 |
| 인증/JWT | 미구현 |
| 고양이 AI 상호작용 | 미구현 |

---

# 12. 이 문서를 쓰는 방법

새 기능 구현이 들어올 때마다:

```text
현재 코드 확인
→ 구현됨/부분/미구현 갱신
→ 관련 시나리오와 일치 확인
```

한다.

문서가 코드보다 앞서 있는 것은 괜찮다.

하지만 **문서에는 구현됐다고 쓰고 실제 코드에는 없는 상태**는 피한다.
