# E. 인증·JWT DB Before / After

이 문서는 인증이 구현될 때 회원가입·로그인·JWT·자동 출석이 **DB와 어떻게 연결되는지** 정리한다.

현재 별도 auth router는 없으므로 대부분 향후 구현 기준이다.

로그인 방식, password_hash, refresh token 등은 정책 확정 전 스키마를 임의로 고정하지 않는다.

---

## E-DB01. 회원가입 — 로컬 인증을 채택할 경우

### Before

```text
USERS에 username=player01 없음
```

### 처리 후보

```text
입력 validation
→ username 유일성 확인
→ password hash 생성
→ USERS INSERT
→ COMMIT
```

### After

```text
USERS.U1
username=player01
password_hash=해시값   # 로컬 인증 채택 시
role=확정 기본값
...
```

비밀번호 원문은 DB에 저장하지 않는다.

---

## E-DB02. 동시 중복 username 가입

username UNIQUE를 채택한다면 두 요청이 동시에 같은 이름으로 가입해도 DB UNIQUE가 최종 방어선이다.

### After 목표

```text
동일 username 사용자 row = 1개
```

사전 SELECT만으로 유일성을 보장하지 않는다.

---

## E-DB03. 로그인 성공 자체

### Before

```text
USERS.U1 존재
저장된 인증 정보 정상
```

### 처리

```text
User 조회
→ 자격증명 검증
```

JWT access token을 stateless하게 발급한다면 토큰 발급 자체는 USERS row를 꼭 수정할 필요가 없다.

### After

인증 자체만 보면 DB 변화 없음일 수 있다.

다만 확정 출석 요구 때문에 **오늘 첫 로그인이라면 출석 DB write가 이어진다.**

---

## E-DB04. 오늘 첫 로그인 + 자동 출석

### Before

```text
USERS.U1.balance = B
오늘 ATTENDANCES(U1, today) 없음
```

### 처리

인증 성공 후 attendance service:

```text
BEGIN
→ ATTENDANCES(U1,today) INSERT
→ UNIQUE 통과
→ USERS.balance = balance + 100
→ COMMIT
```

### After

```text
ATTENDANCES 새 row 1개
USERS.U1.balance = B + 100
```

로그인 Response에 `attendance.granted=true`를 넣을지는 API 계약 선택 사항이다.

---

## E-DB05. 같은 날 재로그인

### Before

```text
오늘 ATTENDANCES(U1,today) 이미 존재
balance = B
```

### 처리

로그인은 정상 인증.

자동 attendance는 `이미 오늘 처리됨`으로 no-op.

### After

```text
attendance row 추가 없음
balance = B
로그인 성공
```

자동 출석 중복 때문에 로그인 전체가 실패하면 안 된다.

---

## E-DB06. 동시 로그인

같은 사용자로 거의 동시에 여러 로그인 요청이 성공한다.

### 목표

`UNIQUE(user_id, check_in_date)` 때문에 자동 출석은 1개만 생성.

### After

```text
오늘 attendance = 1개
100원 지급 = 1회
```

---

## E-DB07. 잘못된 로그인

### Before

User가 없거나 비밀번호가 틀림.

### After

```text
USERS 변경 없음
ATTENDANCES 생성 없음
balance 변경 없음
```

인증 실패 사용자에게 출석 보상을 처리하지 않는다.

---

## E-DB08. JWT 보호 API

JWT가 유효한 경우 서버는 token에서 current_user를 식별한다.

### DB 관점

예를 들어 상점 구매에서:

```text
Request body의 user_id가 아니라 JWT U1
→ USERS.U1 / INVENTORIES.U1을 변경
```

다른 사용자 U2의 row는 바뀌지 않아야 한다.

---

## E-DB09. user_id 위조

### 공격

JWT 사용자 U1이 body/path에 U2 UUID를 보냄.

### After 목표

```text
U2 balance/inventory/house/cats/attendance 등 변화 없음
```

최종 API는 JWT 사용자 기준으로 처리하거나 요청을 거절한다.

---

## E-DB10. role guard

### Before

```text
U1.role = 일반 사용자
```

### 관리자 write 요청

### After

```text
TASKS/ITEMS/CATS 등 master data 변화 없음
```

권한 검사 실패는 DB write 전에 끝낸다.

---

## E-DB11. refresh token — 정책 미정

refresh를 도입하면 저장 전략에 따라 DB Before/After가 달라진다.

후보:

```text
stateless
서버 저장
hash 저장
별도 token table
```

현재 19테이블 구조와 실제 MVP 범위를 고려해 인증 정책을 먼저 정한다.

이 문서에서 새로운 테이블을 확정하지 않는다.

---

## E-DB12. logout — 정책 미정

access-only stateless JWT라면 logout이 DB write 없이 클라이언트 token 삭제일 수 있다.

refresh/revoke 구조가 있으면 DB 상태 변경이 필요할 수 있다.

따라서 logout DB 변화는 token 정책 확정 후 작성한다.

---

## E-DB13. 비밀정보

DB에 저장하더라도 일반 Response로 나가면 안 되는 값:

```text
password_hash
refresh token secret/raw value(채택 방식에 따라)
```

그리고 다음은 DB에 저장하지 않는다.

```text
password 원문
JWT secret
```

---

# 한눈에 보는 핵심

```text
회원가입
인증 방식 확정 → 필요한 USERS 컬럼 확정 → hash 저장

로그인
자격증명 검증 → 성공한 사용자만 자동 출석

자동 출석
Attendance INSERT + 100원 = 같은 transaction

JWT
body/path user_id보다 인증된 current_user가 기준

권한 실패
DB write 전에 종료
```

인증 DB의 목적은 단순히 토큰을 발급하는 것이 아니라 **누가 어떤 사용자 row를 수정할 수 있는지 신뢰 가능한 기준을 만드는 것**이다.
