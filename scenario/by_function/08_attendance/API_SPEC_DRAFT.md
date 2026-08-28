# H. 출석 API 명세 초안

이 문서는 `08_attendance` 시나리오를 실제 API 계약으로 옮기기 위한 초안이다.

현재 `main`에는 수동 check-in endpoint와 출석 기록 조회가 구현돼 있다. 하지만 확정 요구사항은 **매일 자정 이후 첫 로그인 시 자동 출석 처리 + 100원 지급**이므로 최종 통합에서는 로그인 흐름과 연결해야 한다.

서비스 timezone과 연속 출석 추가보상 여부는 아직 미정이다.

---

## 1. 현재 수동 check-in

### Endpoint

```http
POST /users/{user_id}/attendance/check-in
```

### 현재 구현

구현됨.

### 처리

```text
User 존재 확인
→ 서버가 today 계산
→ 이전 Attendance 조회
→ streak 계산
→ ATTENDANCES INSERT
→ flush
→ UNIQUE 충돌 검사
→ USERS.balance + 100
→ COMMIT
```

### 현재 Response

```json
{
  "attendance_id": "uuid",
  "check_in_date": "2026-08-27",
  "streak_count": 3,
  "reward_amount": 100,
  "current_balance": 900
}
```

---

## 2. 확정된 최종 트리거

확정 요구사항:

```text
매일 자정 이후 첫 로그인
→ 자동 출석
→ 100원 지급
```

따라서 최종 사용자 UX에서는 별도 출석 버튼이 없어도 된다.

로그인 성공 후 서버 내부에서 attendance service를 호출하는 구조를 권장한다.

```text
로그인 인증 성공
→ 오늘 출석 처리 시도
→ 이미 오늘 출석했으면 no-op
→ 새 출석이면 100원 지급
→ 로그인 정상 완료
```

---

## 3. 같은 날 두 번째 로그인

매우 중요하다.

현재 수동 check-in endpoint는 같은 날 두 번째 요청에 `409`를 반환한다.

하지만 **자동 출석이 로그인 내부에서 실행될 때는 같은 날 재로그인이 정상적인 행동**이다.

따라서 로그인 서비스에서는 UNIQUE 충돌을:

```text
오늘 이미 출석함
```

으로 해석하고 로그인 자체는 계속 성공시킨다.

즉:

```text
자동 출석 중복
≠ 로그인 실패
```

이다.

---

## 4. DB UNIQUE

핵심 제약:

```text
UNIQUE(user_id, check_in_date)
```

이 제약이 하루 1회 출석의 최종 방어선이다.

프론트에서 출석 버튼을 숨기거나 로그인 시 한 번만 호출한다고 가정하지 않는다.

동시에 여러 로그인/요청이 와도 DB에는 하루 1개 row만 남아야 한다.

---

## 5. 출석 + 보상 transaction

반드시 같이 성공해야 한다.

```text
BEGIN
→ ATTENDANCES INSERT
→ UNIQUE 통과
→ USERS.balance + 100
→ COMMIT
```

중간 reward update가 실패하면:

```text
ROLLBACK
```

되어 attendance row도 남지 않아야 한다.

그렇지 않으면 사용자는 출석은 찍혔는데 보상은 못 받고, 다시 시도하면 UNIQUE 때문에 막히게 된다.

---

## 6. 보상 증가 방식

현재 코드처럼 DB에서 직접 증가시키는 형태가 안전하다.

```sql
UPDATE users
SET balance = balance + :reward
WHERE id = :user_id;
```

Python에서 기존 balance를 읽은 뒤 `old + reward`를 덮어쓰는 방식보다 동시성에 안전하다.

현재 확정 reward는:

```text
100원
```

이다.

---

## 7. streak 계산

현재 구현:

```text
가장 최근 과거 출석 조회
→ 최근 날짜 == 어제
  → 이전 streak + 1
→ 아니면 1
```

### 현재 상태

구현됨.

### 아직 정책 미정

```text
5일/10일 등 milestone 추가 보상
streak 최대 보너스
결석 후 처리
```

기본 streak 계산과 추가 보상 정책은 분리해서 생각한다.

---

## 8. 출석 기록 조회

### Endpoint

```http
GET /users/{user_id}/attendances
```

### 현재 구현

구현됨.

### Response

```json
[
  {
    "id": "uuid",
    "check_in_date": "2026-08-27",
    "streak_count": 3
  }
]
```

JWT 이후 본인 기록은:

```http
GET /me/attendances
```

형태를 검토할 수 있다.

---

## 9. timezone

### 현재 코드

```python
date.today()
```

를 사용한다.

이 방식은 서버 OS timezone에 따라 날짜가 달라질 수 있다.

예:

```text
한국 00:05
UTC 15:05(전날)
```

### 최종 원칙

- 클라이언트가 날짜를 보내지 않음
- 서버가 서비스 timezone 기준으로 오늘을 계산
- 정확한 timezone은 팀에서 확정

한국 대상 서비스라면 `Asia/Seoul`이 이해하기 쉬운 후보지만 팀 확정 전까지 설정값으로 남긴다.

---

## 10. 로그인 Response와 출석 표시

프론트가 자동 출석 보상 팝업을 띄우려면 로그인 Response에 출석 결과를 포함하는 방식이 편하다.

예시 후보:

```json
{
  "access_token": "...",
  "attendance": {
    "granted": true,
    "reward_amount": 100,
    "streak_count": 3
  }
}
```

이미 오늘 출석했다면:

```json
{
  "attendance": {
    "granted": false
  }
}
```

처럼 표현할 수 있다.

이 필드를 login Response에 넣을지, 별도 `/me` 데이터로 받을지는 프론트와 합의한다.

---

## 11. 수동 check-in endpoint를 최종적으로 남길지

현재 endpoint는 개발/Swagger 테스트에는 유용하다.

하지만 자동 출석이 최종 UX라면 일반 사용자용으로 계속 공개할 필요는 없을 수 있다.

후보:

```text
A. 유지하되 로그인도 같은 service 사용
B. 일반 사용자 API에서는 제거하고 내부 service로만 사용
C. 개발/관리자 전용으로 제한
```

이건 API 정리 단계에서 결정한다.

중요한 것은 **자동 출석과 수동 endpoint가 서로 다른 로직을 갖지 않도록 공통 service를 쓰는 것**이다.

---

## 12. 동시 요청

테스트 예:

```text
같은 사용자
같은 날짜
동시 50회 요청
```

기대 결과:

```text
ATTENDANCES row = 1
100원 지급 = 1회
나머지 요청 = 이미 출석 처리
balance 중복 증가 없음
```

UNIQUE + 같은 transaction이 핵심이다.

---

## 13. 존재하지 않는 사용자

현재 수동 endpoint는 User가 없으면 `404`다.

JWT 기반 로그인 자동 출석에서는 이미 인증된 User가 있으므로 이 상황은 일반적으로 발생하지 않아야 한다.

내부 데이터 이상으로 User를 찾지 못하면 로그인/인증 흐름 자체의 오류로 본다.

---

## 14. 재화 구조가 바뀌는 경우

현재 확정 요구사항과 구현은 `USERS.balance + 100` 기준이다.

향후 팀이 재화 구조를 다른 방식으로 **명시적으로 확정**하면:

```text
출석 reward 대상 컬럼
로그인 Response
상점/가챠와의 경제 연결
```

을 함께 수정한다.

그 전까지 문서에서 임의로 사료/금화 구조로 바꾸지 않는다.

---

# H 영역 완료 판정

```text
수동 check-in                 DONE
100원 지급                    DONE
streak 계산                   DONE
UNIQUE 하루 1회               DONE
출석/보상 transaction         DONE
출석 기록 조회                DONE
첫 로그인 자동 출석           MISSING
같은 날 재로그인 no-op 처리   MISSING
login Response 연동           MISSING/POLICY
timezone 명시                 POLICY/MISSING
JWT 사용자 식별              MISSING
추가 streak 보상              POLICY
```

# 구현 전 핵심 결정

1. 서비스 timezone
2. 로그인 Response에 출석 결과를 포함할지
3. 현재 수동 check-in endpoint를 최종적으로 유지할지
4. streak milestone 추가 보상 여부
5. JWT 적용 시 `/me/attendances`로 바꿀지

확정돼 있는 핵심은 바뀌지 않는다.

```text
매일 자정 이후 첫 로그인
→ 자동 출석 1회
→ 100원 지급
```
