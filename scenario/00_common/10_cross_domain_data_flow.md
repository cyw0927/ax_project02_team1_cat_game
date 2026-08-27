# 도메인 간 데이터 흐름

폴더는 기능별로 분리되어 있지만 실제 사용자 행동은 여러 도메인을 연달아 건드린다. 이 문서는 어디까지가 각 도메인의 책임인지 정리한다.

## 1. 학습 → 보상 → 경제

```text
사용자 문제 제출
→ learning이 채점 결과 확정
→ 최초 정답 여부 확인
→ 보상 정책이 확정된 경우 USERS.balance 변경
→ 프론트에 reward/current_balance 반환
```

핵심은 `learning`이 문제의 정답 여부를 판단하고, 재화 자체의 정합성은 `USERS.balance` 변경 규칙을 따른다는 것이다.

## 2. 경제 → 상점 → 하우징

```text
상점 구매
→ economy가 balance 차감
→ INVENTORIES 수량 증가
→ housing은 INVENTORIES를 보고 실제 보유 여부 확인
→ PLACED_OBJECTS에 배치
```

하우징은 가격을 계산하지 않는다. 아이템을 샀는지 여부만 Inventory를 통해 확인한다.

## 3. 경제 → 가챠 → 고양이

```text
가챠 요청
→ balance 차감
→ 확률 정책으로 CATS 선택
→ USER_CATS 소유권 생성
→ 중복 정책이 있으면 mileage 반영
```

가챠는 `cats`와 `users/economy`가 만나는 기능이므로 transaction 경계를 명확히 해야 한다.

## 4. 학습 채점기 → 배틀

배틀 문제도 `TASKS` 문제은행과 같은 채점 엔진을 재사용할 수 있다.

```text
ROOM_TASKS에서 현재 task 확인
→ 사용자 코드 제출
→ sandbox 채점
→ 정답이면 battle 점수 규칙 적용
```

일반 학습 보상과 배틀 점수는 같은 개념이 아니다. 배틀 정답이라고 일반 학습 최초 정답 보상을 자동으로 같이 줄지는 별도 정책이다.

## 5. 학습 채점기 → 승급전

```text
RANK_CHALLENGE_TASKS.task_id
→ TASKS 문제 조회
→ sandbox 채점
→ is_passed 변경
→ 전체 합격 조건 확인
→ RANK_CHALLENGES 상태 변경
```

승급전도 일반 `TASK_ATTEMPTS`와 같은 이력을 남길지, `RANK_CHALLENGE_TASKS`만 사용할지는 설계에서 구분한다.

## 6. 인증 → 모든 도메인

인증이 붙기 전에는 API body/path로 user_id를 받는 임시 구조가 있을 수 있다.

최종적으로는:

```text
JWT
→ 백엔드가 현재 사용자 식별
→ 각 도메인이 current_user.id 사용
```

방향이 안전하다.

따라서 인증 도입 시 learning/economy/housing/battle/ranking API의 `user_id` 입력 위치를 일괄 검토해야 한다.

## 7. USERS를 공유한다고 users 폴더가 모든 로직을 맡는 것은 아님

예:

```text
balance 컬럼은 USERS에 있음
하지만 상점 구매 로직 → economy

wallpaper_item_id는 USERS에 있음
하지만 벽지 변경 로직 → housing

host_user_id는 USERS FK
하지만 방 시작 로직 → battle
```

DB에서 어느 테이블에 컬럼이 있는지와 코드 도메인 책임은 별개다.

## 8. 도메인 간 호출 시 주의

- 같은 비즈니스 규칙을 두 폴더에 복사하지 않는다.
- 보상량, 점수 같은 공통 규칙이 확정되면 설정 위치를 한 곳으로 통일한다.
- 하나의 사용자 요청이 여러 DB 테이블을 바꾸면 transaction 경계를 먼저 결정한다.
- 다른 도메인의 private 로직을 무작정 import해 순환 의존성을 만들지 않는다.

## 9. 전체 핵심 흐름

```text
                ┌→ 상점 → Inventory → Housing
학습 → 보상/재화 ┤
                └→ 가챠 → UserCats → Cat Memory

TASKS/Sandbox ─→ 일반 학습 채점
              ├→ 배틀 채점/점수
              └→ 승급전 채점/합격

Auth ─────────→ 모든 사용자 기능의 신원 확인
```

이 그림을 유지하면 폴더는 나뉘어 있어도 제품 전체 흐름을 잃지 않는다.