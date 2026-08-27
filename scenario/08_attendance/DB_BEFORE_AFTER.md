# H. 출석 DB Before / After

이 문서는 확정 요구사항인 **매일 자정 이후 첫 로그인 자동 출석 + 100원 지급**이 DB에서 어떻게 보장되어야 하는지 정리한다.

현재 수동 check-in transaction은 구현돼 있고 로그인 자동 연결과 명시적 timezone 처리는 아직 남아 있다.

---

## H-DB01. 오늘 첫 출석 — 현재 수동 API 기준

### Before

```text
USERS.U1.balance = B
오늘 ATTENDANCES(U1,today) 없음
```

### 처리

```text
BEGIN
→ User 확인
→ server today 계산
→ 이전 attendance로 streak 계산
→ ATTENDANCES INSERT
→ flush
→ UNIQUE 통과
→ USERS.balance = balance + 100
→ COMMIT
```

### After

```text
ATTENDANCES.A1
user_id=U1
check_in_date=today
streak_count=계산값

USERS.U1.balance = B + 100
```

---

## H-DB02. 같은 날 중복 출석 — 현재

### Before

```text
ATTENDANCES(U1,today) 이미 존재
USERS.U1.balance = B
```

### 새 check-in

INSERT가 복합 UNIQUE와 충돌.

```text
UNIQUE(user_id, check_in_date)
```

### After

```text
attendance row 추가 없음
balance = B
```

현재 수동 API는 `409`를 반환한다.

---

## H-DB03. 동시에 50회 요청

### Before

오늘 출석 없음.

### 동시에

50개 요청이 같은 `(U1,today)`로 INSERT를 시도.

### 목표 After

```text
ATTENDANCES 오늘 row = 1
USERS.balance 증가 = 100 한 번
```

프론트 버튼 잠금이 아니라 DB UNIQUE가 최종 방어선이다.

---

## H-DB04. 연속 출석

### Before

```text
어제 Attendance
check_in_date=yesterday
streak_count=3
```

### 오늘 출석 After

```text
오늘 Attendance.streak_count=4
```

과거 row는 수정하거나 삭제하지 않는다.

---

## H-DB05. 연속 출석 끊김

### Before

마지막 Attendance 날짜가 어제가 아님.

### After

```text
오늘 Attendance.streak_count=1
```

과거 기록은 그대로 남긴다.

---

## H-DB06. 보상 UPDATE 실패

### transaction 중

```text
ATTENDANCES INSERT 성공
→ USERS balance UPDATE 실패
```

### 올바른 처리

```text
ROLLBACK
```

### After

```text
오늘 attendance row 없음
balance = Before와 동일
```

출석만 찍히고 보상은 못 받는 반쪽 상태를 막는다.

---

## H-DB07. 출석 INSERT 실패

UNIQUE 충돌 또는 DB 오류가 먼저 발생하면 reward UPDATE를 진행하지 않는다.

### After

```text
balance 추가 증가 없음
```

---

## H-DB08. 출석 기록 조회

### API

```http
GET /users/{user_id}/attendances
```

### After

DB 변화 없음.

해당 사용자 기록만 최신 날짜순으로 읽는다.

---

## H-DB09. 첫 로그인 자동 출석 — 최종 요구사항

### Before

```text
로그인 인증 성공
오늘 attendance 없음
balance=B
```

### 처리

```text
인증 성공
→ attendance service 호출
→ Attendance + 100 transaction
```

### After

```text
로그인 성공
오늘 attendance 1개
balance=B+100
```

별도 출석 버튼을 눌러야만 보상받는 구조가 최종 요구사항은 아니다.

---

## H-DB10. 같은 날 재로그인 — 향후

### Before

```text
오늘 attendance 이미 있음
balance=B
```

### 로그인

인증은 정상 성공.

attendance service는 이미 출석된 것으로 처리.

### After

```text
로그인 성공
attendance 추가 없음
balance=B
```

자동 출석의 중복 상태를 로그인 장애로 취급하지 않는다.

---

## H-DB11. 동시 로그인 — 향후

같은 사용자 세션에서 여러 로그인 성공이 동시에 이어져도 출석 transaction은 같은 UNIQUE를 사용한다.

### After 목표

```text
오늘 attendance=1
100원=1회
```

---

## H-DB12. 자정 경계

서비스 timezone이 확정되면 서버가 그 timezone에서 `check_in_date`를 계산한다.

예:

```text
service date D 23:59:59 → D
service date D+1 00:00:00 이후 → D+1
```

### After

날짜가 실제 서비스 기준과 일치해야 한다.

클라이언트가 날짜 값을 보내 DB 날짜를 결정하지 않는다.

---

## H-DB13. 서버 OS timezone이 UTC인 경우

현재 `date.today()`는 배포 환경에 따라 위험할 수 있다.

향후 명시적 timezone 계산을 적용하면 OS가 UTC여도 서비스 날짜를 동일하게 판정해야 한다.

### DB 목표

```text
check_in_date = 서비스 기준 오늘
```

---

## H-DB14. JWT ownership

### 공격

JWT 사용자 U1이 U2의 user_id로 출석 처리 시도.

### After 목표

```text
U2 attendance 변화 없음
U2 balance 변화 없음
```

최종 자동 출석은 인증된 current_user 기준이다.

---

## H-DB15. streak 추가 보상 — 정책 미정

향후 milestone 보상을 채택한다면 기본 100원과 별도로 확정된 규칙만 추가한다.

예시 숫자를 임의로 DB 로직에 넣지 않는다.

추가 보상을 넣더라도:

```text
Attendance INSERT
+ 기본 보상
+ milestone 보상
```

이 한 번의 출석 처리에서 중복되지 않도록 transaction/유일성을 같이 검토한다.

---

# 한눈에 보는 핵심

```text
오늘 첫 로그인
Attendance INSERT
→ UNIQUE 통과
→ balance +100
→ COMMIT

같은 날 재로그인
이미 Attendance 존재
→ 보상 없음
→ 로그인은 성공

동시 요청
UNIQUE가 하루 1개만 허용

중간 오류
ROLLBACK
→ 출석과 100원 모두 Before 상태
```

출석 DB의 핵심은 **하루 1회라는 규칙과 100원 지급을 하나의 transaction으로 묶고, 그 최종 방어를 복합 UNIQUE에 맡기는 것**이다.
