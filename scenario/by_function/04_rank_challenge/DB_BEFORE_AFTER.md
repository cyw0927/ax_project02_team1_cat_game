# D. 랭킹·승급전 DB Before / After

이 문서는 승급전 생성, 코드 저장, 채점, TIMEOUT, SUCCESS/FAILED가 **DB에서 어떤 순서로 바뀌어야 하는지** 정리한다.

현재 `main`에는 승급전 생성과 코드 저장까지 구현돼 있고 실제 채점/완료/점수/보상은 아직 없다.

---

## D-DB01. 랭킹 조회

`RANKING_GROUPS`, `RANKING_PARTICIPANTS`를 읽기만 한다.

### After

DB 변화 없음.

랭킹은 `current_rank_score` 기준 정렬 결과만 반환한다.

---

## D-DB02. 정상 승급전 시작 — 현재

### Before

```text
RANKING_PARTICIPANTS에 (G1,U1) 존재
U1/G1의 유효한 IN_PROGRESS challenge 없음
TASKS T1,T2 active
```

### 처리

```text
BEGIN
→ expires_at 미래 확인
→ 참가자 확인
→ active challenge 확인
→ task_ids 중복/active 확인
→ RANK_CHALLENGES INSERT
→ flush로 challenge_id 확보
→ RANK_CHALLENGE_TASKS 순서대로 INSERT
→ COMMIT
```

### After

```text
RANK_CHALLENGES.CH1
user=U1
group=G1
status=IN_PROGRESS
started_at=server now
expires_at=현재 Request 값

RANK_CHALLENGE_TASKS
CT1 challenge=CH1 task=T1 order=1 is_passed=false
CT2 challenge=CH1 task=T2 order=2 is_passed=false
```

challenge와 tasks가 반쪽만 생성되면 안 된다.

---

## D-DB03. 시작 중간 실패 rollback

### 상황

challenge INSERT 후 challenge task 저장 중 오류.

### 처리

```text
ROLLBACK
```

### After

```text
RANK_CHALLENGES 새 row 없음
RANK_CHALLENGE_TASKS 새 row 없음
```

---

## D-DB04. active challenge 중복

### Before

```text
CH1 U1/G1 status=IN_PROGRESS
expires_at > server now
```

### 새 시작 요청

### After

새 challenge 생성 없음.

현재는 SELECT 검사 방식이다. 동시 시작 요청을 얼마나 강하게 막을지 별도 동시성 검토가 필요하다.

---

## D-DB05. 코드 임시 저장 — 현재

### Before

```text
CH1 IN_PROGRESS, 미만료
CT1 saved_code=NULL
```

### 처리

```text
challenge ownership/상태/시간 확인
→ CT1 확인
→ saved_code UPDATE
→ COMMIT
```

### After

```text
CT1.saved_code = 최신 코드
```

다시 저장하면 같은 row를 갱신한다.

---

## D-DB06. 만료 후 코드 저장

### Before

```text
server_now >= CH1.expires_at
```

### 현재 처리

`409`로 거절.

### After

```text
saved_code 변화 없음
```

현재 코드는 CH1.status를 자동 `TIMEOUT`으로 바꾸지는 않는다.

---

## D-DB07. 저장 코드 복원

### Before

```text
CT1.saved_code = "사용자가 작성한 코드"
```

### 재접속

DB row를 읽어 본인에게만 복원한다.

### After

DB 변화 없음.

현재 API는 실제 code 대신 `has_saved_code`만 반환하므로 Response 설계 보완이 필요하다.

---

## D-DB08. 문제 정답 — 향후

### Before

```text
CH1 status=IN_PROGRESS
server_now < expires_at
CT1 is_passed=false
```

Sandbox 결과는 PASSED.

### 처리 후보

```text
BEGIN
→ challenge ownership/상태/만료 재확인
→ CT1.is_passed=true
→ 전체 합격 조건 확인
→ 아직 완료 아님이면 COMMIT
```

### After

```text
CT1.is_passed=true
CH1.status=IN_PROGRESS   # 아직 다른 문제가 남았다면
```

---

## D-DB09. 최종 문제 통과 → SUCCESS — 향후

### Before

```text
CH1 IN_PROGRESS
합격 조건 직전까지 충족
마지막 필요한 task만 미통과
```

### 처리 목표

```text
BEGIN
→ challenge 상태/만료 재확인
→ 마지막 task 통과 반영
→ 합격 기준 충족 확인
→ CH1 IN_PROGRESS → SUCCESS
→ RANKING_PARTICIPANTS.current_rank_score 변경
→ 성공 보상 반영
→ COMMIT
```

### After

```text
CH1.status=SUCCESS
필요 task is_passed=true
rank score=서버 규칙 반영값
보상=최초 1회만 반영
```

정확한 점수/보상량은 POLICY.

---

## D-DB10. SUCCESS 재처리

### Before

```text
CH1 status=SUCCESS
이미 점수/보상 반영 완료
```

### 같은 완료 로직 재호출

### After 목표

```text
CH1 계속 SUCCESS
rank score 추가 증가 없음
보상 추가 지급 없음
```

상태 전이 최초 성공을 1회성 기준으로 사용한다.

---

## D-DB11. TIMEOUT — 향후

### Before

```text
CH1 status=IN_PROGRESS
server_now >= expires_at
```

### 처리 후보

```text
BEGIN
→ status/시간 재확인
→ CH1.status=TIMEOUT
→ COMMIT
```

### After

```text
CH1.status=TIMEOUT
```

보상/성공 점수는 반영하지 않는다.

lazy timeout인지 별도 정리 작업인지 구현 방식은 선택 가능하지만 서버 시각이 기준이다.

---

## D-DB12. 만료 경계 정답 제출

### 위험

채점 시작 때는 미만료였지만 Docker 실행이 끝난 시점에는 만료될 수 있다.

### 원칙

최종 DB 반영 transaction에서 `expires_at`을 다시 확인한다.

### After

경계 처리 정책에 따라 SUCCESS 또는 TIMEOUT 중 하나로만 일관되게 확정되어야 한다.

정확한 경계 규칙은 POLICY.

---

## D-DB13. FAILED — 정책 미정

FAILED가 되는 조건이 확정되면:

```text
IN_PROGRESS → FAILED
```

최초 전환 시 점수 감소/보상이 있다면 같은 transaction에서 처리한다.

현재는 실패 조건과 점수 정책을 임의로 넣지 않는다.

---

## D-DB14. 서버 재시작

### Before

메모리 상태는 사라짐.

DB에는:

```text
CH1.status
started_at
expires_at
CT*.task_order
is_passed
saved_code
```

가 남아 있다.

### After

DB를 읽어서:

```text
미만료 → 이어하기 정책
만료 → TIMEOUT 확정
```

으로 복구한다.

---

# 한눈에 보는 핵심

```text
승급전 시작
challenge + challenge_tasks = 같은 transaction

autosave
기존 challenge_task row UPDATE

채점 완료
최종 DB 반영 때 status와 expires_at 재확인

SUCCESS
상태 + rank score + 보상 = 최초 1회 transaction

TIMEOUT
클라이언트 타이머가 아니라 서버 시각 기준
```

승급전 DB는 **서버 재시작 후에도 이어갈 수 있는 영속 상태**와 **SUCCESS 보상 중복 방지**가 핵심이다.
