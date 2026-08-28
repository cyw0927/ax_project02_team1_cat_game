# 보상 1회 지급 설계

이 문서는 학습·출석·배틀·승급전에서 **같은 이벤트의 보상이 두 번 이상 지급되지 않도록** 설계하는 기준을 정리한다.

핵심 질문은 다음이다.

```text
이 보상은 어떤 사건에 대해 정확히 한 번만 지급되어야 하는가?
```

---

## 1. 왜 필요한가

다음 상황에서 중복 보상이 생길 수 있다.

- 사용자가 버튼을 연타
- HTTP 요청 재전송
- 서버 응답 유실 후 재시도
- worker가 같은 작업을 두 번 실행
- finish/completion API가 중복 호출
- 서버 복구 과정에서 같은 이벤트 재처리

프론트 버튼 잠금은 최종 방어가 아니다.

---

## 2. 출석

가장 단순한 1회 보상 구조다.

```text
UNIQUE(user_id, check_in_date)
```

를 기준으로:

```text
ATTENDANCES INSERT
→ 성공한 transaction에서만 보상 지급
```

한다.

같은 날짜 두 번째 요청은 UNIQUE 충돌로 차단할 수 있다.

---

## 3. 학습 최초 정답 보상

문제:

같은 사용자/같은 문제의 두 attempt가 거의 동시에 PASSED 될 수 있다.

원하는 규칙이:

```text
사용자 1명 + task 1개
→ 최초 정답 보상 1회
```

이라면 해당 사실을 원자적으로 보장해야 한다.

현재 ERD에는 별도 reward history 테이블이 없다.

후보:

A. 사용자 row를 짧게 FOR UPDATE하고 과거 PASSED 재확인
B. 별도 UNIQUE 보상 기록 구조 추가
C. TASK_ATTEMPTS에 reward_granted 성격 컬럼을 추가하되, 이것만으로 user-task 전체 1회를 보장할 수 있는지 추가 검토

정확한 방식은 학습 보상 규칙 확정 후 선택한다.

---

## 4. 승급전 성공 보상

상대적으로 단순하다.

```text
IN_PROGRESS → SUCCESS
```

상태가 **처음 바뀌는 transaction** 안에서 보상을 지급한다.

이미 SUCCESS인 challenge에 같은 완료 로직이 다시 들어오면:

```text
상태 전이 없음
→ 보상도 없음
```

이어야 한다.

즉 상태 전이를 보상 발생 조건으로 사용한다.

---

## 5. 배틀 종료 보상

현재 가장 큰 미정 영역이다.

```text
IN_PROGRESS → FINISHED
```

상태 전이만으로 room이 한 번 끝났다는 것은 막을 수 있지만, 여러 참가자에게 어떤 보상을 이미 줬는지 추적하는 문제는 별개다.

예:

```text
room FINISHED
user A 지급 성공
user B 지급 성공
user C 지급 중 DB 오류
```

전체를 한 transaction으로 묶으면 rollback할 수 있지만 참가자가 많아지거나 정책이 복잡해질수록 별도 지급 이력이 유리할 수 있다.

현재 ERD에는 battle reward history가 없다.

따라서 배틀 보상 실제 구현 전 구조 결정을 P0로 본다.

---

## 6. 가챠는 '보상'과 조금 다름

가챠는 사용자가 재화를 소비하고 결과를 받는 transaction이다.

```text
재화 차감
+ USER_CATS 획득
+ mileage/교환권 처리
```

가 모두 같이 성공해야 한다.

같은 요청이 네트워크 재전송되었을 때 두 번 뽑히게 할지 막을지는 idempotency 정책과 연결된다.

가챠는 의도한 두 번 클릭과 네트워크 중복을 구분해야 하므로 단순 UNIQUE만으로 해결하기 어렵다.

필요하면 request idempotency key를 검토한다.

---

## 7. 상점 구매도 마찬가지

상점은 여러 번 구매가 정상일 수 있다.

따라서:

```text
같은 item 구매
= 무조건 중복 오류
```

로 만들 수 없다.

문제는 **같은 구매 요청이 네트워크 때문에 다시 전송된 것인지** 여부다.

MVP에서는 버튼 잠금 + Atomic Update + transaction으로 시작하고, 실제 중복 결제가 문제가 되면 idempotency key를 추가 검토한다.

---

## 8. exactly-once와 현실

분산 시스템에서 완벽한 exactly-once 처리는 복잡하다.

MVP에서 목표는:

```text
같은 이벤트를 다시 처리해도
중복 지급되지 않는 멱등한 완료 로직
```

에 가깝다.

특히 보상은 다음처럼 생각하면 된다.

```text
보상 발생 조건을 DB 상태/UNIQUE와 연결
→ transaction 안에서 조건 확인 + 지급
→ commit
```

---

## 9. 재화 변경은 서버 기준

프론트에서:

```json
{"reward": 5000}
```

같이 보내고 서버가 믿으면 안 된다.

보상량은 서버의 기획 설정/DB 기준으로 계산한다.

---

## 10. 실패와 재시도

좋은 흐름:

```text
BEGIN
→ 보상 자격 확인
→ 상태 전이/유일성 확보
→ 재화 변경
→ 관련 결과 저장
→ COMMIT
```

중간 실패:

```text
ROLLBACK
```

한다.

응답만 유실됐는데 commit은 성공한 경우 다시 호출해도 **이미 처리됨을 인식하고 추가 지급하지 않아야 한다.**

---

## 11. 현재 도메인별 방어 수단

| 기능 | 1회 기준 | 현재 활용 가능한 핵심 수단 |
| --- | --- | --- |
| 출석 | user + date | UNIQUE |
| 학습 보상 | user + task + 보상규칙 | 추가 설계 필요 |
| 승급전 | challenge SUCCESS 최초 전이 | 상태 전이 + transaction |
| 배틀 보상 | room 결과 + participant | 추가 설계 필요 |
| 상점 | 구매 요청 자체 | Atomic Update + transaction, 필요 시 idempotency |
| 가챠 | pull 요청 자체 | transaction, 필요 시 idempotency |

---

## 12. 테스트

- 출석 2회 동시 호출
- 동일 task 두 정답 동시 완료
- 승급전 success 완료 로직 2회
- battle finish 2회
- 응답 직전 connection 끊고 같은 요청 재시도
- transaction 중간 오류
- 보상 성공 후 같은 이벤트 재처리

---

# 결론

보상 코드를 작성하기 전에 항상 먼저 적는다.

```text
1. 무엇을 1회라고 볼 것인가?
2. 그 1회를 DB에서 어떻게 증명할 것인가?
3. 어느 transaction에서 지급할 것인가?
4. 같은 로직을 다시 실행해도 안전한가?
```

이 네 질문에 답하지 못하면 보상 구현을 완료 처리하지 않는다.