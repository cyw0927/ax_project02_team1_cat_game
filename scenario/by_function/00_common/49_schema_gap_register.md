# 스키마 갭 등록부

이 문서는 현재 19개 테이블 ERD와 최신 시나리오 사이에서 **현재 컬럼만으로 표현이 부족한 지점**을 모아둔다.

중요:

- 여기 적힌 항목은 `필요 가능성` 또는 `설계 결정을 먼저 해야 하는 지점`이다.
- 이 문서만 보고 migration을 바로 만들지 않는다.
- 20개 미만 테이블 제한을 유지해야 한다면 새 테이블보다 기존 테이블 확장으로 해결 가능한지도 먼저 검토한다.

---

## 1. USERS — 인증 정보 부족

현재 주요 컬럼:

```text
id
username
role
balance
mileage
house_level
wallpaper_item_id
floor_item_id
created_at
```

로컬 로그인 방식이라면 부족할 수 있는 후보:

```text
password_hash
email(필요 시)
account status / deleted flag(탈퇴 정책이 필요할 경우)
```

또한 `username UNIQUE` 여부도 인증 설계와 함께 확정해야 한다.

### 결론

**인증 방식 확정 전 migration 금지.**

---

## 2. USERS — 재화 종류 확장 가능성

현재는:

```text
balance
mileage
```

두 값이다.

향후 실제 게임 재화가:

```text
일반 재화
고급 재화
가챠 mileage
```

처럼 3종으로 확정되면 현재 구조만으로는 의미가 모호해진다.

후보:

- USERS에 명확한 재화 컬럼 추가
- 기존 balance/mileage 의미 재정의
- 별도 wallet 구조

다만 **재화 기획이 아직 최종 확정되지 않은 상태라면 먼저 컬럼을 만들지 않는다.**

---

## 3. TASKS — 사용자용 문제 지문 부족

현재:

```text
concept_id
type
difficulty
template_code
test_cases
is_active
```

가 있다.

학습 화면에서 문제를 읽기 위해 다음이 필요할 수 있다.

```text
title
description
```

현재 A-01 상세 시나리오에서 이미 갭으로 기록돼 있다.

### 영향

- 문제 상세 API
- 프론트 학습 화면
- 관리자 문제 등록

---

## 4. TASK_ATTEMPTS — 결과 표현 부족

현재:

```text
submitted_code
status
is_correct
used_hint
attempted_at
```

이다.

후보 갭:

```text
result_message
started_at
completed_at
```

특히 RuntimeError나 시스템 오류를 polling 후 사용자에게 다시 보여주려면 결과 메시지 저장 위치가 필요하다.

또한 PENDING 상태에서 `is_correct=False`가 저장되므로 의미상:

```text
아직 결과 없음
```

과

```text
오답
```

을 status로만 구분하게 된다.

`is_correct nullable` 전환 여부도 검토할 수 있으나 필수는 아니다.

---

## 5. 학습 최초 정답 보상 기록

현재 TASK_ATTEMPTS만으로 과거 PASSED를 조회해 최초 보상을 판단할 수는 있다.

하지만 동시에 여러 attempt가 PASSED가 되면:

```text
둘 다 이전 PASSED 없음 확인
→ 둘 다 보상
```

위험이 있다.

후보:

- USERS row lock 후 과거 결과 재확인
- 별도 reward history
- 기존 테이블에 reward_granted 같은 상태 추가

19테이블 제한을 고려하면 **새 테이블 추가 전 기존 구조에서 안전하게 해결 가능한지 먼저 결정**한다.

---

## 6. ROOMS — 실제 경기 진행상태 정보 부족

현재:

```text
id
title
host_user_id
status
max_participants
```

만 있다.

실제 배틀에서 필요해질 수 있는 후보:

```text
created_at
started_at
finished_at
current_task_order
```

현재 WebSocket 재접속 시:

```text
몇 번째 문제를 진행 중인가?
```

를 DB snapshot만으로 복구하려면 별도 진행상태가 필요할 수 있다.

다만 배틀 진행 방식을 먼저 확정한다.

---

## 7. 배틀 사용자별·문제별 득점 기록 부족

현재:

```text
ROOM_PARTICIPANTS.current_score
ROOM_TASKS
```

는 있지만 다음 사실을 영속적으로 저장하지 않는다.

```text
user A가 room X의 task Y에서 이미 점수를 받았는가?
```

이 기록이 없으면 같은 문제를 반복 제출해 중복 득점하는 것을 안전하게 막기 어렵다.

후보:

A. 별도 battle attempt/score 테이블
B. 기존 TASK_ATTEMPTS를 배틀까지 확장
C. ROOM_TASKS/ROOM_PARTICIPANTS에 구조 확장
D. 메모리에서만 기록

D는 서버 재시작/재접속에 약하므로 최종 DB 설계가 필요하다.

### 중요

이 항목은 실제 배틀 scoring 구현 전 **P0 설계 결정**이다.

---

## 8. 배틀 보상 1회 지급 기록 부족

현재 `ROOMS.status=FINISHED`는 결과 완료는 표현하지만:

```text
이 방의 결과 보상이 이미 지급됐는가?
```

를 별도로 표현하지 않는다.

finish 재호출이나 서버 재처리 시 중복 보상 위험이 있다.

후보:

- ROOMS에 reward_processed 정보
- 별도 reward ledger
- 상태 전이 최초 성공 transaction으로만 보상

정확한 구조는 배틀 보상 규칙과 함께 결정한다.

---

## 9. RANK_CHALLENGES — 완료/보상 추적

현재:

```text
status
started_at
expires_at
```

가 있다.

`IN_PROGRESS → SUCCESS` 최초 전환 transaction 안에서 보상을 지급하면 별도 flag 없이도 단순화할 수 있다.

하지만 복잡한 retry가 필요해지면:

```text
reward_processed
completed_at
```

같은 정보가 도움이 될 수 있다.

MVP에서는 먼저 상태 전이 자체로 1회성을 해결 가능한지 본다.

---

## 10. ITEMS — 판매 중지 표현 부족

현재:

```text
category
name
price
```

뿐이다.

이미 사용자가 보유한 item을 삭제하지 않고 신규 판매만 막고 싶다면:

```text
is_active
```

같은 상태가 필요할 수 있다.

물리 DELETE보다 비활성화가 과거 Inventory 참조를 보존하기 쉽다.

---

## 11. CATS — 가챠 후보 제외 상태 부족

현재:

```text
name
persona
rarity
```

가 있다.

특정 고양이를 신규 가챠 풀에서만 빼고 기존 소유자는 유지하려면:

```text
is_active / is_gacha_available
```

같은 표현이 필요할 수 있다.

가챠 풀 관리 방식이 설정 기반이라면 반드시 컬럼이 필요한 것은 아니다.

---

## 12. USER_CATS — 고양이 하우징 배치 정보 부족

최신 제품 흐름:

```text
가챠
→ 고양이 획득
→ 하우징에 배치
```

현재 USER_CATS는:

```text
id
user_id
cat_id
```

만 가진다.

PLACED_OBJECTS는 `item_id`만 참조하므로 고양이 위치를 저장할 수 없다.

따라서 고양이를 실제 하우징 공간에 보여줄 경우 다음을 결정해야 한다.

후보:

- USER_CATS에 position/placed 상태 추가
- 별도 cat placement 구조
- 하우징에서 고양이는 위치 저장 없이 단순 노출

### 중요

UI가 고양이를 자유롭게 움직이는 방식인지, 사용자가 직접 배치하는 방식인지 먼저 확정한다.

---

## 13. USER_CATS — 중복 고양이 정책

현재 `(user_id, cat_id)` UNIQUE가 없다.

따라서 DB 구조상 같은 cat master를 여러 USER_CATS row로 소유하는 것이 가능하다.

이것이 의도인지 다음을 결정해야 한다.

```text
중복 고양이 여러 마리 소유
vs
중복은 mileage/다른 보상으로 전환
```

가챠 구현 전에 반드시 확인한다.

---

## 14. CAT_MEMORIES — 한 고양이당 몇 row인가

현재 `user_cat_id` UNIQUE가 없다.

따라서 한 USER_CAT에 여러 memory row를 둘 수 있다.

하지만 시나리오상 단순한 최신 `context_summary` 하나만 유지한다면:

```text
user_cat_id UNIQUE
```

를 검토할 수 있다.

여러 기억 조각을 쌓을 계획이면 일반 index가 맞다.

---

## 15. 하우징 position_data 검증

현재 JSONB 하나로 자유롭게 저장한다.

최종적으로:

```json
{"x": 2, "y": 3, "rotation": 90}
```

같은 구조가 확정되면 서버 validation을 추가할 수 있다.

DB JSONB 자체는 유지 가능하므로 반드시 migration이 필요한 문제는 아니다.

---

# 우선순위

## P0 — 실제 핵심 구현 전에 결정

```text
배틀 문제별 중복 득점 기록
가챠 중복 USER_CATS 정책
고양이 하우징 배치 표현 방식
인증 방식/USERS 컬럼
재화 구조(실제 2종 이상 채택 시)
```

## P1 — 해당 화면 완성 전 결정

```text
TASKS title/description
TASK_ATTEMPTS result_message/timestamp
ITEMS 판매중지
CATS 가챠 활성상태
```

## P2 — 운영 고도화

```text
세밀한 completed_at/audit 정보
CAT_MEMORIES 장기 기억 구조
추가 운영 이력
```

---

# migration 만들기 전 체크

```text
1. 이 갭이 실제 확정 요구사항인가?
2. 코드만으로 해결 가능한가?
3. 기존 19테이블 구조를 유지할 수 있는가?
4. 새 컬럼이 기존 데이터에 nullable/default 문제를 만들지 않는가?
5. 프론트/API Response도 같이 바뀌는가?
6. 다른 팀원이 같은 모델 migration을 만들고 있지 않은가?
```

이 질문을 통과한 것만 Alembic 변경으로 만든다.
