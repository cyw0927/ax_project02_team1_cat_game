# 테이블별 CRUD 매트릭스

이 문서는 19개 ERD 테이블이 **어느 기능에서 읽히고(Read), 생성되고(Create), 수정되고(Update), 삭제되는지(Delete)** 한눈에 보기 위한 공통 문서다.

목적은 단순하다.

```text
어떤 API를 만들었는데
→ 내가 건드리는 테이블이 무엇인지 모르겠다
→ 다른 팀원 기능을 깨뜨릴 수 있다
```

이 문제를 줄이기 위해 테이블별 책임 범위를 명확히 한다.

> 아직 미정인 기능은 `예정`, 이미 시나리오상 필요한 것은 `필요`, 현재 구현 여부는 별도로 본다.

---

## 1. USERS

### 역할
모든 사용자 데이터의 기준점. 기본 프로필과 재화, 하우징 메타 정보를 가진다.

### 읽기
- 로그인 사용자 확인
- 학습 제출 시 사용자 존재 확인
- 상점/가챠 잔액 확인
- 하우징 wallpaper/floor 조회
- 배틀/랭킹 사용자 확인
- 출석 사용자 확인

### 생성
- 회원가입 시 사용자 생성

### 수정
- 재화 증가/감소
- mileage 변경
- wallpaper/floor 변경
- 향후 인증 정보 컬럼이 들어가면 비밀번호 hash 등

### 삭제
MVP에서는 사용자 물리 삭제는 가급적 피하고 별도 정책 필요.

### 주의
여러 도메인이 가장 많이 공유하는 테이블이라 migration 충돌 위험이 크다.

---

## 2. ATTENDANCES

### 읽기
- 출석 기록 조회
- 연속 출석 계산
- 오늘 출석 여부 확인(UX용)

### 생성
- 당일 출석 체크 성공 시 1행

### 수정
보통 없음. 생성 당시 streak_count를 확정해서 기록.

### 삭제
운영 데이터이므로 일반 사용자 API에서는 없음.

### 핵심 제약
`UNIQUE(user_id, check_in_date)`

---

## 3. CONCEPTS

### 읽기
- 학습 개념 목록
- 문제의 개념명 표시
- 사용자 숙련도 표시

### 생성/수정/삭제
관리자 기능이 생기면 가능. 일반 사용자 API에서는 Read 위주.

---

## 4. TASKS

### 읽기
- 학습 문제 목록/상세
- Docker 채점 시 `test_cases`
- 배틀 ROOM_TASKS 구성
- 승급전 문제 구성

### 생성/수정
관리자 문제 등록/수정 기능이 생길 경우.

### 삭제
물리 삭제보다 `is_active=false` 소프트 비활성화를 우선.

### 주의
프론트 Response에 `test_cases`를 노출하지 않는다.

---

## 5. USER_PROFICIENCY

### 읽기
- 사용자 단원별 숙련도
- 추천 문제 알고리즘

### 생성
사용자가 특정 concept를 처음 학습할 때 초기 row 생성 가능.

### 수정
정답/학습 결과에 따라 proficiency_level 변경.

### 삭제
일반적으로 없음.

### 미정
증가/감소 공식과 범위.

---

## 6. TASK_ATTEMPTS

### 읽기
- 제출 결과 polling
- 사용자 과거 시도 목록
- 최초 정답 여부 확인

### 생성
- 일반 학습 문제 제출마다 새 row

### 수정
- `PENDING → RUNNING → 최종상태`
- `is_correct` 확정

### 삭제
감사 로그 성격이라 일반적으로 삭제하지 않음.

### 중요
기존 시도를 UPDATE해서 재제출하는 것이 아니라 **재제출마다 새 row**를 만든다.

---

## 7. ROOMS

### 읽기
- 배틀 방 목록
- 방 상세
- 입장 가능 상태
- 방장 확인

### 생성
- 방 생성

### 수정
- WAITING → IN_PROGRESS → FINISHED

### 삭제
방 삭제 기능을 둘 경우 WAITING에서만 허용하는 등 정책 필요.

### 동시성
방 입장처럼 참가자 수를 함께 판단할 때 row를 `FOR UPDATE`로 잠글 수 있다.

---

## 8. ROOM_PARTICIPANTS

### 읽기
- 참가자 목록
- Ready 상태
- 현재 점수
- 팀별 score 집계

### 생성
- 방 참가
- 방장 자동 참가 정책이면 방 생성과 동시에 생성 가능

### 수정
- `is_ready`
- `current_score`
- 필요 시 team_name

### 삭제
- WAITING 상태에서 퇴장
- IN_PROGRESS 중 삭제는 정책 미정

### 핵심 제약
`UNIQUE(room_id, user_id)`

---

## 9. ROOM_TASKS

### 읽기
- 배틀 중 문제 순서 확인

### 생성
- 방 시작 전 문제 구성

### 수정
일반적으로 task_order를 만든 뒤에는 변경 최소화.

### 삭제
WAITING에서만 방장이 문제 제거 가능.

### 제약
- `UNIQUE(room_id, task_id)`
- `UNIQUE(room_id, task_order)`

---

## 10. RANKING_GROUPS

### 읽기
- 랭킹 그룹 목록/상세
- 그룹 랭킹 조회

### 생성
- 그룹 생성 기능이 있을 경우 owner가 생성

### 수정/삭제
owner/admin 권한 정책 필요.

---

## 11. RANKING_PARTICIPANTS

### 읽기
- 그룹 랭킹
- 승급전 시작 자격

### 생성
- 사용자가 ranking group에 참가

### 수정
- `current_rank_score`

### 삭제
그룹 탈퇴 정책이 있을 경우.

### 제약
`UNIQUE(group_id, user_id)`

---

## 12. RANK_CHALLENGES

### 읽기
- 현재 진행 중 승급전
- 과거 승급전 결과
- expires_at 확인

### 생성
- 승급전 시작

### 수정
- `IN_PROGRESS → SUCCESS/FAILED/TIMEOUT`

### 삭제
감사/기록 성격 때문에 일반적으로 없음.

### 중요
한 사용자에게 동시에 여러 active challenge를 허용할지 정책 필요. 현재 추천은 1개.

---

## 13. RANK_CHALLENGE_TASKS

### 읽기
- 승급전 문제 순서
- saved_code 복원
- is_passed 확인

### 생성
- 승급전 시작 시 문제 수만큼 생성

### 수정
- saved_code
- is_passed

### 삭제
challenge 기록과 함께 보존 권장.

---

## 14. ITEMS

### 읽기
- 상점 상품 목록
- 가격 조회
- 하우징 category 확인

### 생성/수정
관리자 상품 등록/가격 변경 기능이 있을 경우.

### 삭제
이미 구매 이력이 연결되어 있으므로 물리 삭제보다 판매 중지 정책 검토.

---

## 15. INVENTORIES

### 읽기
- 사용자 보유 아이템
- 하우징 배치 가능 수량
- wallpaper/floor 소유권

### 생성
- 첫 구매

### 수정
- 동일 item 재구매 시 quantity 증가

### 삭제
아이템 소비 기능이 생기면 quantity 감소 후 0 처리 정책 필요.

### 제약
`UNIQUE(user_id, item_id)`

---

## 16. PLACED_OBJECTS

### 읽기
- 하우스 렌더링

### 생성
- 가구 배치

### 수정
- 이동
- 회전

### 삭제
- 방에서 치우기

### 주의
삭제해도 Inventory 소유 수량은 줄이지 않는다.

---

## 17. CATS

### 읽기
- 가챠 후보
- 보유 고양이 상세
- persona/rarity

### 생성/수정
관리자 고양이 마스터 등록 기능이 있을 경우.

### 삭제
기존 USER_CATS가 참조하므로 물리 삭제 주의.

---

## 18. USER_CATS

### 읽기
- 사용자 보유 고양이 목록
- 대화 전 소유권 확인

### 생성
- 가챠 성공 결과

### 수정
현재 ERD 기준 거의 없음.

### 삭제
고양이 판매/방출 기능이 없다면 없음.

### 미정
중복 고양이를 별도 인스턴스로 여러 row 허용할지, UNIQUE로 한 마리 소유만 허용할지.

---

## 19. CAT_MEMORIES

### 읽기
- 고양이 대화 전 과거 context_summary 조회

### 생성
- 첫 메모리 요약 저장

### 수정
- 새 대화 요약으로 context_summary 갱신

### 삭제
사용자가 기억 초기화 기능을 원할 경우에만 검토.

---

# 도메인별 주 담당 테이블 요약

| 도메인 | 주 테이블 |
| --- | --- |
| users/auth | USERS, ATTENDANCES |
| learning | CONCEPTS, TASKS, USER_PROFICIENCY, TASK_ATTEMPTS |
| battle | ROOMS, ROOM_PARTICIPANTS, ROOM_TASKS |
| ranking | RANKING_GROUPS, RANKING_PARTICIPANTS, RANK_CHALLENGES, RANK_CHALLENGE_TASKS |
| economy/shop | ITEMS, INVENTORIES, USERS(balance) |
| housing | PLACED_OBJECTS, INVENTORIES, USERS(wallpaper/floor) |
| cats/gacha | CATS, USER_CATS, CAT_MEMORIES, USERS(재화/mileage) |

# 핵심 원칙

1. 같은 테이블을 여러 도메인이 사용한다고 해서 파일을 한 곳으로 합칠 필요는 없다.
2. 테이블의 **소유 도메인**과 다른 도메인의 **참조 사용**을 구분한다.
3. USERS처럼 공유도가 높은 테이블 변경은 팀 합의 후 migration을 만든다.
4. 감사 로그 성격의 TASK_ATTEMPTS/RANK_CHALLENGES는 함부로 DELETE하지 않는다.
5. Read만 하는 API에는 억지로 Lock을 사용하지 않는다.
