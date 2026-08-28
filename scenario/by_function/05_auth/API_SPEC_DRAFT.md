# E. 인증·JWT API 명세 초안

이 문서는 `05_auth` 시나리오를 실제 인증 API 계약으로 옮기기 위한 초안이다.

현재 `main`에는 별도 auth router가 없고, 대부분의 쓰기 API가 path/body의 `user_id`를 직접 받는다. 따라서 이 문서는 **현재 구현**과 **추가 필요**를 분리해 적는다.

토큰 만료시간, refresh token 사용 여부, 이메일 로그인 여부 등은 아직 정책 미정이므로 임의로 확정하지 않는다.

---

## 1. 현재 상태

현재 USERS에는 다음 주요 값이 있다.

```text
id
username
role
balance
mileage
house_level
...
```

하지만 로컬 아이디/비밀번호 로그인을 하려면 보통 다음 정보가 추가로 필요하다.

```text
password_hash
username UNIQUE 여부
```

이메일이 실제 로그인/복구에 필요할 때만 `email` 추가를 검토한다.

### 현재 판정

```text
회원가입        MISSING
로그인          MISSING
JWT 발급        MISSING
JWT 검증        MISSING
/me             MISSING
role guard      MISSING
```

---

## 2. 회원가입

### Endpoint 후보

```http
POST /auth/register
```

### Request 후보

```json
{
  "username": "player01",
  "password": "..."
}
```

### 서버 처리

```text
입력 형식 검증
→ username 중복 확인
→ password 원문을 hash
→ USERS 생성
→ COMMIT
```

### 절대 금지

- 비밀번호 원문 DB 저장
- 비밀번호 원문 로그 기록
- Response에 password/hash 노출

### 상태코드 후보

- 성공: `201 Created`
- username 중복: `409 Conflict`
- 형식 오류: `422` 또는 팀 공통 validation 정책

### 스키마 선행조건

로컬 인증을 채택한다면 `password_hash`와 username 유일성 정책부터 migration으로 확정해야 한다.

---

## 3. 로그인

### Endpoint 후보

```http
POST /auth/login
```

### Request 후보

```json
{
  "username": "player01",
  "password": "..."
}
```

### 서버 처리

```text
username으로 User 조회
→ password hash 검증
→ 인증 성공
→ 매일 자정 이후 첫 로그인 자동 출석 처리
→ 토큰 발급
→ 로그인 Response
```

### 중요

현재 확정된 출석 요구사항:

```text
매일 자정 이후 첫 로그인
→ 출석 1회 기록
→ 100원 지급
```

따라서 로그인 성공 흐름과 출석 서비스가 연결되어야 한다.

같은 날 두 번째 로그인에서 출석 UNIQUE 충돌이 발생하더라도 **로그인 자체가 실패하면 안 된다.**

---

## 4. 로그인 Response 후보

JWT를 사용한다면 예:

```json
{
  "access_token": "...",
  "token_type": "bearer",
  "user": {
    "id": "user-uuid",
    "username": "player01",
    "role": "..."
  },
  "attendance": {
    "granted": true,
    "reward_amount": 100
  }
}
```

`attendance`를 로그인 Response에 포함할지는 프론트 UX와 합의한다.

같은 날 이미 출석했다면:

```json
{
  "attendance": {
    "granted": false
  }
}
```

같은 형태로 표현할 수 있다.

---

## 5. 인증 실패

잘못된 username/password는 인증 정보 노출을 최소화한다.

예:

```http
401 Unauthorized
```

Response 후보:

```json
{
  "detail": "Invalid credentials"
}
```

`username은 존재하지만 password만 틀림` 같은 정보를 공격자에게 구체적으로 알려줄 필요는 없다.

---

## 6. JWT 사용자 식별

로그인 이후 보호 API는 최종적으로:

```text
Authorization: Bearer <token>
```

에서 사용자를 식별한다.

현재처럼:

```json
{
  "user_id": "다른 사람 UUID"
}
```

를 보내도 서버가 그 값을 신뢰해서는 안 된다.

### 최종 원칙

```text
내 자산 변경
→ JWT user_id 기준
```

적용 대상 예:

- 상점 구매
- 가챠
- 내 하우스 수정
- 출석
- 문제 제출
- 배틀 Ready/Start
- 승급전
- 고양이 대화

---

## 7. 현재 사용자 조회

### Endpoint 후보

```http
GET /me
```

### Response 후보

```json
{
  "id": "user-uuid",
  "username": "player01",
  "role": "...",
  "balance": 0,
  "mileage": 0,
  "house_level": 1
}
```

재화 구조가 바뀌면 Response도 같이 변경한다.

다른 사용자 프로필 공개 API와 `/me`는 목적을 분리한다.

---

## 8. 401과 403

구분한다.

```text
401 = 로그인/토큰이 유효하지 않음
403 = 로그인은 됐지만 그 행동 권한이 없음
```

예:

```text
토큰 만료 → 401
일반 user가 관리자 API → 403
방 참가자가 아닌데 해당 방 제어 → 403/404 정책 통일
```

---

## 9. role 권한

현재 USERS.role 컬럼은 존재하지만 실제 guard는 없다.

관리자 API를 만들 경우:

```text
JWT 검증
→ current_user.role 확인
→ 권한 없으면 403
```

형태로 처리한다.

프론트에서 메뉴를 숨기는 것만으로 권한 검사를 끝내지 않는다.

---

## 10. access token 만료

### 정책 미정

결정할 것:

```text
access token 만료시간
refresh token 사용 여부
refresh token 저장 위치
로그아웃 시 서버측 폐기 필요 여부
```

MVP에서 구조를 단순하게 할지, refresh까지 포함할지는 팀 범위에 따라 정한다.

숫자를 문서에서 임의로 정하지 않는다.

---

## 11. refresh token

사용할 경우 Endpoint 후보:

```http
POST /auth/refresh
```

하지만 refresh 사용 여부 자체가 미정이므로 현재는 **POLICY** 상태다.

DB에 refresh token을 그대로 저장하는 방식, hash 저장, stateless 방식 등은 실제 인증 정책 확정 후 결정한다.

---

## 12. logout

### Endpoint 후보

```http
POST /auth/logout
```

JWT를 완전 stateless로 운영한다면 서버가 access token을 즉시 무효화하기 어렵다.

따라서 logout의 의미는 refresh 구조와 함께 확정한다.

현재는 **POLICY**.

---

## 13. WebSocket 인증

배틀 WebSocket도 인증이 필요하다.

연결 시:

```text
token 검증
→ user 식별
→ room 존재
→ ROOM_PARTICIPANTS에 해당 user 존재
→ 연결 허용
```

query에 `user_id`만 넣어 다른 사용자로 접속하게 해서는 안 된다.

토큰 전달 방식은 브라우저/프론트 구현 방식과 합의한다.

---

## 14. 기존 API의 user_id 제거 전략

JWT 도입 시 모든 endpoint를 제각각 바꾸지 않고 관련 API를 묶어서 전환한다.

예:

```text
POST /shop/buy
현재: {user_id, item_id}
최종 후보: {item_id}
```

```text
POST /attempts
현재: {user_id, task_id, submitted_code}
최종 후보: {task_id, submitted_code}
```

```text
PATCH /rooms/{room_id}/participants/{user_id}/ready
최종 후보: JWT 사용자 자신의 Ready 변경 endpoint로 단순화
```

프론트와 Request 계약을 동시에 맞춘다.

---

## 15. 자동 출석과 로그인 transaction

로그인 인증 자체와 출석 DB 변경을 하나의 거대한 transaction으로 묶을 필요는 없다.

핵심은:

```text
인증 성공
→ 자동 출석 서비스 호출
```

후 출석 내부에서:

```text
ATTENDANCES INSERT
+ 100원 지급
= 같은 transaction
```

으로 보장하는 것이다.

이미 오늘 출석했다면 no-op으로 처리하고 로그인은 계속 성공한다.

---

# E 영역 완료 판정

```text
USERS 기본 모델              DONE
회원가입                     MISSING/POLICY
password_hash                MISSING/POLICY
username UNIQUE              POLICY
로그인                       MISSING
자동 출석 로그인 연결        MISSING
JWT 발급/검증                MISSING
/me                          MISSING
role guard                   MISSING
refresh                      POLICY
logout                       POLICY
WebSocket 인증               MISSING
기존 user_id 제거            MISSING
```

# 구현 전 핵심 결정

1. 로컬 아이디/비밀번호인지 소셜 로그인인지
2. username UNIQUE 여부
3. password_hash 컬럼
4. email 필요 여부
5. access token 만료 정책
6. refresh 사용 여부
7. logout 의미
8. role 기본값/관리자 범위
9. 서비스 timezone

인증 방식을 먼저 확정한 뒤 USERS migration과 API 구현을 같이 맞춘다.
