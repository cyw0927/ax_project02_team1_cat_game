# H. 출석 테스트 케이스

표기:

- **NOW**: 현재 수동 check-in 코드로 테스트 가능
- **AFTER**: 로그인 자동 출석 연결 후 테스트
- **POLICY**: timezone·추가 streak 보상 확정 후 기대값 고정

확정 요구사항:

```text
매일 자정 이후 첫 로그인
→ 자동 출석 1회
→ 100원 지급
```

---

## H-T01. 오늘 첫 수동 check-in — NOW

`POST /users/{user_id}/attendance/check-in`

**Then**
- ATTENDANCES 1개 생성
- streak 계산
- balance +100
- Response reward_amount=100

---

## H-T02. 같은 날 중복 check-in — NOW

같은 날짜에 두 번째 요청.

**Then**
- `409`
- attendance row 추가 없음
- balance 추가 증가 없음

---

## H-T03. 동시 50회 check-in — NOW

같은 user/date로 동시에 여러 요청을 보낸다.

**Then**
- ATTENDANCES row = 1
- 100원 지급 = 1회
- balance 중복 증가 없음

`UNIQUE(user_id, check_in_date)`가 최종 방어선이다.

---

## H-T04. 연속 출석 — NOW

어제 streak=3인 기록을 준비하고 오늘 출석한다.

**Then** 오늘 streak=4.

---

## H-T05. 연속 출석 끊김 — NOW

마지막 출석이 이틀 이상 전이면 오늘 streak=1.

---

## H-T06. 월말/연말 경계 — NOW

날짜가 월/년을 넘어가도 어제 판정과 streak 계산이 올바른지 확인한다.

---

## H-T07. 존재하지 않는 사용자 — NOW

`404`, ATTENDANCES/USERS balance 변화 없음.

---

## H-T08. 보상 UPDATE 실패 rollback — NOW 테스트 작성 필요

Attendance INSERT 후 balance UPDATE에서 DB 오류를 강제로 발생시킨다.

**Then**
- 전체 rollback
- attendance row도 남지 않음
- balance도 변화 없음

---

## H-T09. 출석 기록 조회 — NOW

`GET /users/{user_id}/attendances`

**Then**
- 해당 user 기록만 반환
- 최신 날짜순
- DB 변경 없음

---

## H-T10. 첫 로그인 자동 출석 — AFTER

오늘 첫 로그인 성공 시 내부 attendance service가 자동 실행된다.

**Then**
- 로그인 성공
- attendance 1개
- balance +100
- 필요하면 로그인 Response에 granted=true

---

## H-T11. 같은 날 두 번째 로그인 — AFTER

**Then**
- 로그인은 정상 성공
- attendance 추가 없음
- balance 추가 지급 없음
- granted=false 등 프론트 계약에 맞는 결과

중복 출석 때문에 login 전체가 실패하면 안 된다.

---

## H-T12. 동시 로그인 — AFTER

같은 user로 동시에 로그인해도 하루 출석과 100원은 1회만 처리돼야 한다.

---

## H-T13. 자정 직전/직후 — AFTER/POLICY

서비스 timezone 기준:

```text
23:59:59
00:00:00 이후
```

를 나눠 테스트한다.

정확한 timezone은 팀 확정값을 사용한다.

---

## H-T14. 서버 OS timezone 차이 — AFTER/POLICY

서버 OS timezone이 UTC여도 서비스 기준 날짜가 정확히 계산되는지 확인한다.

현재 `date.today()` 의존을 제거한 뒤 필수 테스트.

---

## H-T15. 클라이언트 날짜 조작 — AFTER

Request에서 날짜를 보내거나 PC 시간을 바꿔도 출석 날짜는 서버가 결정해야 한다.

---

## H-T16. JWT ownership — AFTER

사용자 A가 B의 user_id로 출석을 실행해 B에게 100원을 지급할 수 없어야 한다.

최종 자동 출석은 인증된 current_user 기준.

---

## H-T17. 수동 endpoint와 자동 service 일치 — AFTER

수동 endpoint를 유지한다면 자동 로그인과 동일한 내부 attendance service를 사용해 중복 규칙/transaction이 달라지지 않는지 확인한다.

---

## H-T18. streak milestone — AFTER/POLICY

추가 보상을 실제로 채택할 경우에만 5일/10일 등 확정 milestone을 테스트한다.

현재 100원 기본 출석과 추가 streak 보상은 구분한다.

---

# H 완료 기준

```text
서버 날짜
→ 하루 UNIQUE
→ Attendance + 100원 같은 transaction
→ 동시요청 1회성
→ 첫 로그인 자동 연결
→ 같은 날 재로그인 no-op
```

까지 통과해야 최종 출석 요구사항이 완료된다.
