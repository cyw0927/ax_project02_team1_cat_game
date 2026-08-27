# Migration 변경 계획 초안

이 문서는 현재 스키마 갭을 발견했다고 해서 바로 Alembic migration을 여러 개 만들지 않도록 **무엇을 어떤 순서로 확정하고 변경할지** 정리한다.

핵심:

```text
시나리오 확정
→ API 계약 확인
→ 스키마 변경 필요성 확인
→ 팀원과 migration 충돌 확인
→ Alembic 작성
→ 기존 데이터/테스트 확인
```

---

# Phase 0. 지금 당장 migration을 만들지 않는 항목

아직 비즈니스 규칙이 확정되지 않은 다음 항목은 문서만 유지한다.

```text
가챠 확률/천장 관련 컬럼
배틀 점수 기록 구조
배틀 보상 지급 기록
재화 2종 이상 구조
고양이 하우징 배치 구조
refresh token 저장 구조
```

이유:

나중에 결정이 바뀌면 불필요한 컬럼/테이블과 migration history만 늘어난다.

---

# Phase 1. 학습 화면·채점 완성에 필요한 최소 변경 후보

## 1. TASKS title / description

문제 상세 화면에서 실제 지문이 필요하다는 UX가 확정되면 후보:

```text
title
summary/description
```

기존 TASK row가 있다면 새 NOT NULL 컬럼을 바로 추가하지 말고:

```text
nullable 추가
→ 데이터 채우기
→ 필요하면 NOT NULL 전환
```

순서를 검토한다.

## 2. TASK_ATTEMPTS 결과 정보

RuntimeError/SystemError 메시지를 polling으로 보여주기로 확정하면 후보:

```text
result_message nullable
```

PENDING/RUNNING 시간을 세밀하게 운영할 필요가 확정되면:

```text
started_at
completed_at
```

을 별도 검토한다.

필요 없는 timestamp를 미리 추가하지 않는다.

---

# Phase 2. 인증 방식 확정 후 USERS 변경

로컬 username/password 로그인이라면 후보:

```text
password_hash
username UNIQUE
```

email 기반 기능이 실제 요구되면:

```text
email
email UNIQUE 여부
```

를 별도로 결정한다.

소셜 로그인 중심이라면 필요한 컬럼 구조가 달라질 수 있으므로 **인증 결정 전에 password 컬럼부터 만들지 않는다.**

---

# Phase 3. 재화 기획 확정 후 경제 모델 변경

현재:

```text
USERS.balance
USERS.mileage
```

이다.

만약 최종안이:

```text
일반 재화
고급 재화
mileage
```

3개라면 명확한 컬럼 확장이 필요할 수 있다.

migration과 동시에 확인할 API:

```text
유저 프로필
출석
학습 보상
상점
가챠
배틀 보상
승급전 보상
```

즉 경제 migration은 한 도메인만의 변경이 아니다.

---

# Phase 4. 배틀 scoring 구조 확정 후 변경

가장 먼저 결정:

```text
user-room-task의 1회 득점을 어디에 기록할 것인가?
```

후보별 migration 영향:

### 별도 테이블

가장 표현력은 좋지만 20개 미만 테이블 제한과 충돌할 수 있다.

### 기존 TASK_ATTEMPTS 확장

학습/배틀/승급전 attempt를 공통화할 수 있지만 현재 모델 의미가 크게 바뀐다.

### 기존 battle 테이블 컬럼 확장

테이블 수는 유지하지만 여러 문제별 이력을 표현하기 어려울 수 있다.

결론:

**코드부터 만들지 말고 데이터 모델 결정부터 한다.**

그 다음 함께 검토:

```text
room 진행 위치
시작/종료 timestamp
보상 지급 1회성
```

---

# Phase 5. 고양이 배치 방식 확정

현재 USER_CATS에는 위치 정보가 없다.

사용자가 고양이를 하우징에 직접 배치하기로 확정하면 후보:

```text
USER_CATS.position_data JSONB nullable
USER_CATS.is_placed
```

같은 기존 테이블 확장도 가능하다.

반대로 고양이가 게임 화면에서 자동으로 돌아다닌다면 사용자 직접 배치 좌표가 필요 없을 수도 있다.

그래서 애니메이션/UI 방식이 먼저다.

---

# Phase 6. 마스터데이터 비활성화

필요가 확정되면:

```text
ITEMS.is_active
CATS.is_active 또는 가챠 사용 가능 상태
```

를 검토한다.

TASKS는 이미 `is_active`가 있으므로 같은 운영 개념을 참고할 수 있다.

---

# Migration 하나의 크기

좋은 예:

```text
add task display fields
add auth credentials
add attempt result metadata
```

처럼 목적이 분명한 변경.

피할 것:

```text
20개 컬럼을 한 migration에 한꺼번에 추가
+ 서로 다른 도메인 정책까지 동시에 변경
```

문제가 생겼을 때 원인과 rollback 범위가 너무 커진다.

---

# 3명 협업 시 규칙

migration을 만들기 전 팀에 공유:

```text
내가 어떤 model을 바꾸는가
현재 alembic head가 무엇인가
다른 팀원이 migration 작업 중인가
```

특히 공유 모델:

```text
USERS
TASKS
TASK_ATTEMPTS
```

는 동시에 여러 명이 수정하지 않도록 조율한다.

---

# 기존 데이터가 있을 때

새 컬럼을 추가할 때 항상 묻는다.

```text
기존 row에는 어떤 값이 들어가는가?
nullable인가?
default가 필요한가?
backfill은 어떻게 하는가?
```

예를 들어 기존 사용자 100명이 있는데 `password_hash NOT NULL`을 바로 추가하면 migration이 실패할 수 있다.

---

# Migration 검증

최소:

```text
alembic upgrade head
서버 실행
Swagger 기본 조회
새 컬럼 포함 기능 테스트
가능하면 깨끗한 DB에서 처음부터 upgrade
```

그리고 downgrade를 실제 프로젝트에서 지원할지 여부는 팀 정책에 따르되 migration 파일 자체가 생성되는지 확인한다.

---

# 현재 추천 결정 순서

```text
1. 학습 test_cases/status/결과 표현
2. 인증 방식
3. 재화 최종 구조
4. 가챠 중복 정책
5. 배틀 scoring 데이터 구조
6. 고양이 하우징 배치 방식
7. 운영용 active 상태
```

이 순서는 강제 일정이 아니라 **스키마 변경이 다른 도메인에 미치는 영향이 큰 순서**를 정리한 것이다.

---

# 결론

Migration은 기획을 결정하는 도구가 아니다.

```text
기획/시나리오가 결정됨
→ 현재 DB로 표현 가능한지 확인
→ 정말 부족할 때 migration
```

순서로 진행한다.
