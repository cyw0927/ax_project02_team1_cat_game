# 데이터 소유권 / 권한 매트릭스

이 문서는 사용자가 어떤 데이터를 볼 수 있고, 어떤 데이터를 수정할 수 있는지 정리한다.

인증이 붙기 전에는 `user_id`를 body/path로 받는 임시 API가 있을 수 있지만, 최종적으로는 JWT에서 현재 사용자를 식별하는 방향을 기준으로 한다.

핵심 질문은 항상 이것이다.

```text
이 데이터는 누구 것인가?
누가 읽을 수 있는가?
누가 수정할 수 있는가?
```

---

## USERS

### 본인
- 자기 프로필 조회 가능
- 자기 재화 조회 가능
- wallpaper/floor 변경 가능

### 다른 사용자
- 공개 프로필 범위만 조회 허용 가능
- balance/mileage 같은 내부 자산은 비공개 권장

### 관리자
- role 정책에 따라 관리 가능

---

## ATTENDANCES

### 본인
- 자기 출석 이력 조회
- 자기 출석 체크

### 다른 사용자
- 일반적으로 조회 불필요

### 보안
사용자가 `user_id`를 바꿔 다른 사람 출석을 대신 체크하면 안 된다.
JWT 이후에는 현재 사용자 기준으로만 처리.

---

## TASKS / CONCEPTS

### 일반 사용자
- 활성 문제/개념 조회 가능
- `test_cases`는 절대 노출하지 않음

### 관리자
- 문제 등록/수정/비활성화 기능이 생기면 role 검사 필요

---

## TASK_ATTEMPTS

### 본인
- 자신의 제출 이력/결과 조회 가능

### 다른 사용자
- 다른 사람 submitted_code와 결과는 기본 비공개 권장

### 관리자
- 교육 운영 목적이면 조회 가능 여부 별도 정책

### 중요
`GET /attempts/{attempt_id}`는 단순 UUID만 알면 다른 사람 결과를 볼 수 없도록 최종 인증 단계에서 ownership 검사가 필요하다.

---

## ROOMS

### 일반 사용자
- 공개 방 목록/상태 조회 가능

### 방장
- start/finish
- WAITING 단계의 ROOM_TASKS 관리
- 필요 시 방 삭제

### 참가자
- Ready 변경
- 게임 진행 중 자신의 제출

### 비참가자
- 점수판 공개 여부는 기획 선택
- 쓰기 작업은 금지

---

## ROOM_PARTICIPANTS

### 본인 참가 row
- Ready 변경 가능
- 필요 시 WAITING에서 퇴장

### 다른 참가자
- 이름/Ready/점수 등 게임에 필요한 공개 상태 조회 가능
- 다른 사용자의 is_ready/current_score 직접 수정 금지

### 점수 수정
프론트가 `score=999999`를 보내서 수정하는 구조 금지.

```text
채점 성공
→ 서버가 점수 규칙 계산
→ 서버가 current_score 증가
```

---

## ROOM_TASKS

### 일반 참가자
- 게임 진행 중 필요한 문제 정보 조회
- test_cases는 비공개

### 방장
- WAITING에서 문제 구성 가능 여부

### IN_PROGRESS 이후
문제 목록 변경 금지 권장.

---

## RANKING_GROUPS

### 참가자/일반 사용자
- 공개 그룹이라면 목록/랭킹 조회

### owner
- 그룹 설정 변경 가능 여부
- 멤버 관리 기능이 생기면 owner 검사

### 관리자
- 전체 관리 정책 가능

---

## RANKING_PARTICIPANTS

### 본인
- 자신의 score 조회

### 같은 그룹 사용자
- 랭킹 표시를 위해 username/score 조회 가능

### score 수정
클라이언트가 직접 score를 정해 보내지 않는다.

```text
승급전/게임 결과
→ 서버 계산
→ current_rank_score 변경
```

---

## RANK_CHALLENGES / RANK_CHALLENGE_TASKS

### 본인
- 자기 승급전 조회
- 자기 saved_code 저장
- 자기 문제 제출

### 다른 사용자
- 조회/수정 금지

### ownership 검사

```text
challenge.user_id == current_user.id
```

확인 후 저장/제출.

---

## ITEMS

### 일반 사용자
- 상점 판매 상품 조회 가능

### 관리자
- 가격/상품 등록 변경은 관리자 전용

### 중요
프론트가 price를 보내더라도 믿지 않고 서버가 ITEMS.price를 사용.

---

## INVENTORIES

### 본인
- 자기 보유 아이템 조회 가능

### 다른 사용자
- 일반적으로 직접 Inventory 전체 조회 불필요
- 하우스 방문 때 배치된 결과만 보이면 충분

### 변경
구매/소비 같은 서버 비즈니스 로직을 통해서만 변경.

---

## PLACED_OBJECTS

### 본인
- 배치/이동/회전/삭제

### 다른 사용자
- 하우스 방문을 위한 Read만 가능

### 필수 검사

```text
placed_object.user_id == current_user.id
```

다른 사람 가구를 PATCH/DELETE하면 안 된다.

---

## CATS

### 일반 사용자
- 공개 가능한 고양이 마스터 정보 조회

### 내부 정보
가챠 확률 테이블을 CATS에 직접 저장하지 않는다면 별도 정책.

---

## USER_CATS

### 본인
- 보유 고양이 전체 조회
- 대화 대상 선택

### 다른 사용자
- 하우징에서 공개 고양이만 보여줄지 기획 선택

### 변경
가챠 결과 등 서버 로직으로 생성.

---

## CAT_MEMORIES

### 본인
- 해당 user_cat을 소유한 사용자만 대화 context에 사용

### 다른 사용자
- 절대 조회 금지 권장

고양이 메모리는 개인 대화 내용 요약이므로 가장 강하게 ownership을 확인해야 한다.

---

# 권한 체크를 어디서 하나

최종 인증 도입 후 추천 구조:

```text
JWT decode
→ current_user 식별
→ endpoint별 ownership/role 검사
→ DB 처리
```

프론트가:

```json
{"user_id": "다른사람UUID"}
```

를 보내더라도 그 값으로 소유권을 결정하지 않는다.

---

# 403과 404 선택

예:
사용자가 다른 사람의 private resource ID를 요청했다.

선택지:

```text
403 Forbidden
= 존재하지만 권한 없음

404 Not Found
= 사용자에게 존재 여부도 숨김
```

MVP에서는 명확한 개발 편의를 위해 403을 사용할 수 있다. 보안 민감 리소스는 404로 감추는 방식도 가능하다.

팀에서 공통 기준을 맞추는 것이 중요하다.

---

# 권한 테스트 필수 항목

1. A 사용자가 B의 가구 PATCH 시도
2. A 사용자가 B의 challenge saved_code 수정 시도
3. 일반 참가자가 room start 시도
4. 사용자가 자신의 score를 직접 조작하는 요청 시도
5. 다른 사용자의 CAT_MEMORIES 접근 시도
6. 일반 사용자가 관리자 문제 수정 API 접근

모두 서버에서 거부되어야 한다.
