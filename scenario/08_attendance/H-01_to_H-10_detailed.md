# H-01 ~ H-10. 출석 상세 시나리오

이 문서는 하루 1회 출석 보상, 연속 출석, 중복 요청, 자정 경계, transaction 실패를 정리한다.

> 현재 핵심 방어 원칙은 `ATTENDANCES(user_id, check_in_date)` 복합 UNIQUE다.

---

# H-01. 오늘 첫 출석

## 목적
오늘 처음 출석한 사용자의 출석 기록을 만들고 보상을 지급한다.

## 흐름
```text
첫 로그인 또는 출석 버튼
→ 현재 사용자 확인
→ 서버 기준 오늘 날짜 계산
→ ATTENDANCES INSERT
→ 성공하면 보상 반영
→ COMMIT
→ 출석 완료 응답
```

## DB
- `USERS`
- `ATTENDANCES`

## 핵심
먼저 `오늘 출석했나?`를 SELECT해서 믿는 방식보다 실제 INSERT + UNIQUE 제약을 최종 기준으로 사용한다.

## 테스트
- 오늘 기록 없음 → 성공
- DB에 오늘 날짜가 정확히 저장되는지
- 보상이 한 번만 증가하는지

---

# H-02. 연속 출석

## 목적
전날에도 출석했다면 streak_count를 이어간다.

## 처리
```text
오늘 출석 시도
→ 직전 출석 날짜/연속일 확인
→ 마지막 출석일 == 어제
→ streak_count = 이전 streak + 1
→ 오늘 row INSERT
```

## 왜 streak를 row에 저장하나
매번 처음 가입일부터 모든 출석 행을 세지 않고 해당 출석 시점의 연속일 수를 바로 알 수 있다.

## 테스트
- 어제 streak=3 → 오늘 4
- 월말/연말 날짜 경계

---

# H-03. 연속 출석 끊김

## 상황
마지막 출석이 어제가 아니라 이틀 이상 전이다.

## 처리
```text
마지막 출석 날짜 != 어제
→ streak_count = 1
```

과거 기록을 삭제하지 않는다. 이전 streak는 이력으로 남는다.

## 테스트
- 하루 결석 후 출석
- 여러 달 만에 출석

---

# H-04. 같은 날 중복 출석

## 상황
사용자가 이미 오늘 출석했는데 다시 요청한다.

## DB 방어
```text
UNIQUE(user_id, check_in_date)
```

두 번째 INSERT는 DB가 거절한다.

## 서버
`IntegrityError`를 잡아 rollback하고 `이미 출석했습니다` 응답을 반환한다.

## 왜 이것이 강한가
프론트 버튼을 숨기거나 서버가 사전 SELECT만 하는 것보다 DB 자체가 중복 데이터 생성을 금지하기 때문이다.

---

# H-05. 동시에 수십 번 출석 요청

## 상황
악의적인 사용자가 자정에 50개 요청을 동시에 보낸다.

## Lock 없는 사전 SELECT의 문제
모든 요청이 거의 동시에 `오늘 기록 없음`을 볼 수 있다.

## UNIQUE 방식
50개가 INSERT를 시도해도 `(user_id,date)`가 같은 행은 최종적으로 한 개만 존재할 수 있다.

## 보상 주의
출석 INSERT와 보상 지급은 같은 transaction 흐름 안에서 묶어야 한다. UNIQUE에 성공한 요청만 보상을 지급하도록 순서를 설계한다.

## 테스트
동시 요청 후:
```text
ATTENDANCES 오늘 row 수 = 1
balance 증가 횟수 = 1
```
인지 확인한다.

---

# H-06. 존재하지 않는 사용자

## 상황
가짜 user_id로 출석 API를 호출한다.

## 처리
```text
User 확인
→ 없음
→ 404
→ Attendance INSERT 없음
```

JWT가 도입되면 URL/body의 user_id 대신 인증된 현재 사용자 기준으로 처리하는 방향이 안전하다.

## 테스트
없는 UUID, 삭제된 사용자 등을 확인한다.

---

# H-07. 정상 보상 지급

## 목적
출석 기록이 성공했을 때만 재화를 지급한다.

## 처리 순서
```text
BEGIN
→ 출석 INSERT
→ UNIQUE 통과
→ USERS balance 증가
→ COMMIT
```

## 재화 증가
감소와 마찬가지로 Python에서 기존 값을 읽어 계산해 덮어쓰기보다 DB에서:
```sql
UPDATE users
SET balance = balance + :reward
WHERE id = :user_id;
```
처럼 증가시키는 것이 동시성에 안전하다.

## 보상량
다시 전달된 요구사항에는 100원 예시/정책이 적혀 있지만 최종 기획 문서에서 실제 게임 재화 단위를 다시 확인한 뒤 상수/설정값으로 관리하는 것이 좋다.

## Response
현재 streak와 변경 후 balance를 함께 주면 프론트 갱신이 쉽다.

---

# H-08. 보상 처리 실패 시 rollback

## 상황
Attendance INSERT는 성공했지만 balance UPDATE 중 DB 오류가 발생한다.

## 위험
출석 기록은 생겼는데 돈을 못 받으면 다음 요청은 UNIQUE 때문에 다시 받을 수도 없다.

## 해결
Attendance INSERT와 balance UPDATE를 같은 transaction에 둔다.

```text
INSERT attendance
→ balance UPDATE 실패
→ ROLLBACK
→ attendance INSERT도 취소
```

사용자는 정상 복구 후 다시 출석할 수 있다.

## 테스트
보상 UPDATE 실패를 의도적으로 만들어 attendance row가 남지 않는지 확인한다.

---

# H-09. 출석 기록 조회

## 목적
달력/연속 출석 UI에서 사용자의 과거 출석을 보여준다.

## 흐름
```text
출석 달력 열기
→ 현재 user의 ATTENDANCES 조회
→ 날짜순 또는 최신순 정렬
→ check_in_date/streak_count 반환
```

## DB 변경
없음.

## 페이지네이션
출석 기록이 아주 길어질 경우 기간 필터나 페이지네이션을 넣을 수 있지만 MVP에서는 사용자별 데이터가 많지 않아 단순 조회로 시작할 수 있다.

## 테스트
- 기록 없음
- 여러 날짜 기록
- 다른 사용자 기록이 섞이지 않는지

---

# H-10. 자정 경계와 서버 날짜

## 문제
사용자 PC 시간이 아니라 어떤 시간대를 기준으로 '오늘'을 정할지 명확해야 한다.

예:
```text
한국 00:01
서버가 UTC 기준이면 전날 15:01
```

서버가 단순 `date.today()`를 쓰면 배포 서버의 timezone에 따라 결과가 달라질 수 있다.

## 해결 방향
서비스 기준 timezone을 하나 정하고 서버가 그 timezone으로 `check_in_date`를 계산한다.

한국 사용자 대상이라면 `Asia/Seoul`을 명시적으로 사용하는 안을 검토할 수 있다. 이것도 서비스 운영지역과 기획 확인 후 확정한다.

## 중요한 원칙
클라이언트가 `오늘 날짜`를 body로 보내게 하지 않는다. 사용자가 PC 날짜를 바꿔 출석을 조작할 수 있기 때문이다.

## 테스트
- 23:59 직전
- 00:00 직후
- 서버 timezone이 UTC인 환경

---

# H 영역에서 팀이 확정/검토해야 할 것

1. 출석이 자동인지 버튼식인지
2. 실제 출석 보상량
3. streak 추가 보상이 있는지
4. 서비스 기준 timezone
5. `date.today()` 대신 명시적 timezone 계산 적용 여부
6. 중복 출석 응답을 409로 통일할지
7. 출석 기록 조회 기간/페이지네이션 필요 여부
8. JWT 도입 후 user_id 전달 제거 시점

핵심 구현 원칙은 `복합 UNIQUE + IntegrityError 처리 + 출석/보상 같은 transaction`이다.
