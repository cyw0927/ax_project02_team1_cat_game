# API 의존성 그래프

이 문서는 각 API가 어떤 다른 도메인/테이블/공통 기능에 의존하는지 정리한다.

목적은 한 기능을 수정했을 때 어디까지 영향이 퍼지는지 미리 보는 것이다.

```text
인증
 ↓
사용자 식별
 ↓
학습 / 상점 / 가챠 / 하우징 / 배틀 / 랭킹 / 출석
```

즉 인증은 거의 모든 쓰기 API의 앞단에 놓인다.

---

# 1. 학습 문제 조회

```text
GET /tasks/{task_id}
```

의존:
- TASKS
- 필요 시 CONCEPTS

독립적:
- Docker 불필요
- USERS 불필요(공개 문제 조회라면)

---

# 2. 일반 문제 제출

```text
POST /attempts
```

의존:
- 인증/USERS
- TASKS
- TASK_ATTEMPTS
- 이후 BackgroundTasks
- Sandbox/Docker

후속 의존:
- 채점 성공 시 USERS 재화
- USER_PROFICIENCY

즉 제출 API는 learning만의 기능처럼 보여도 실제로는 다음 흐름을 가진다.

```text
learning
→ sandbox
→ economy(보상)
```

---

# 3. 상점 구매

```text
POST /shop/buy
```

의존:
- 인증/USERS
- ITEMS
- INVENTORIES

DB transaction 하나로 묶인다.

housing은 상점 API를 직접 호출하지 않지만, 구매 결과인 INVENTORIES를 읽는다.

```text
shop
→ INVENTORIES
→ housing
```

---

# 4. 가챠

```text
POST /gacha/pulls
```

의존:
- 인증/USERS
- CATS
- USER_CATS
- mileage 정책

후속:
- 획득한 USER_CATS는 하우징/고양이 대화에서 사용

```text
economy
→ gacha
→ cats
→ housing/social
```

---

# 5. 하우징

가구 배치:

```text
POST /users/{user_id}/house/objects
```

의존:
- 인증/USERS
- INVENTORIES
- ITEMS
- PLACED_OBJECTS

즉 하우징은 상점과 직접 결합하지 않고 **인벤토리 소유 결과**에만 의존한다.

좋은 구조:

```text
상점 구매
→ INVENTORIES

하우징
→ INVENTORIES 확인
```

나쁜 구조:

```text
하우징 코드가 shop.buy 내부 함수를 직접 호출
```

도메인은 DB 계약을 통해 느슨하게 연결하는 것이 좋다.

---

# 6. 배틀 방 입장

```text
POST /rooms/{room_id}/join
```

의존:
- 인증/USERS
- ROOMS
- ROOM_PARTICIPANTS

동시성:
- ROOMS row FOR UPDATE

학습/Docker에는 아직 의존하지 않는다.

---

# 7. 배틀 문제 제출/점수

의존:
- ROOM_PARTICIPANTS
- ROOM_TASKS
- TASKS
- Sandbox/Docker

정답 판정 후:
- current_score 갱신
- WebSocket broadcast

```text
battle
→ learning(TASKS)
→ sandbox
→ battle score
→ websocket
```

주의: 일반 TASK_ATTEMPTS를 배틀 제출에도 그대로 사용할지는 별도 결정 필요. 현재 ERD에는 배틀 전용 attempt 테이블이 없다.

---

# 8. 배틀 종료/보상

의존:
- ROOMS
- ROOM_PARTICIPANTS
- USERS 재화

```text
score 집계
→ 승자 판정
→ FINISHED
→ 보상
```

중복 보상 방지 구조가 아직 핵심 미정이다.

---

# 9. 승급전 시작

의존:
- 인증/USERS
- RANKING_GROUPS
- RANKING_PARTICIPANTS
- TASKS
- RANK_CHALLENGES
- RANK_CHALLENGE_TASKS

```text
ranking participant 확인
→ task 선택
→ challenge 생성
```

---

# 10. 승급전 제출

의존:
- RANK_CHALLENGES
- RANK_CHALLENGE_TASKS
- TASKS
- Sandbox/Docker

성공 완료 시:
- RANKING_PARTICIPANTS score
- USERS 보상

```text
ranking
→ learning(TASKS)
→ sandbox
→ ranking score
→ economy reward
```

---

# 11. 출석

의존:
- 인증/USERS
- ATTENDANCES
- USERS 재화

다른 도메인 의존은 적다.

```text
attendance insert
→ reward
```

그래서 독립적으로 테스트하기 좋은 기능이다.

---

# 12. 인증이 붙기 전/후 차이

현재 임시 구조:

```text
Request body/path
→ user_id
```

최종 구조:

```text
JWT
→ backend가 user_id 추출
```

인증이 붙으면 다음 API들의 Request가 바뀔 수 있다.

- attempts
- shop
- gacha
- house
- attendance
- room join/ready
- ranking challenge

따라서 Auth는 늦게 구현하더라도 API 계약 문서에는 `JWT 이후 user_id 제거 가능`을 계속 표시한다.

---

# 의존성 위험도

## 낮음
- concepts 조회
- tasks 조회
- cats 마스터 조회
- items 조회

## 중간
- attendance
- housing 단순 배치
- ranking 조회

## 높음
- 일반 채점
- 가챠
- 상점 구매
- 방 입장
- 배틀 점수
- 배틀 종료 보상
- 승급전 완료

높은 이유는 transaction, Docker, 재화, lock, 실시간 상태가 섞이기 때문이다.

# 3명 분업 시 핵심

A가 learning/sandbox를 수정하면 C의 battle/ranking 채점에도 영향이 갈 수 있다.

B가 USERS 재화 구조를 변경하면 A의 학습 보상과 C의 배틀/승급전 보상에도 영향이 간다.

C가 인증을 붙이면 A/B의 Request에서 user_id가 사라질 수 있다.

따라서 아래 세 가지 변경은 반드시 공유한다.

```text
TASKS/test_cases 구조 변경
USERS 재화 구조 변경
인증 사용자 식별 방식 변경
```
