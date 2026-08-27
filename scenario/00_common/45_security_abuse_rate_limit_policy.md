# 어뷰징·요청 제한 정책

이 문서는 사용자가 버튼을 연타하거나 자동화 스크립트로 API를 반복 호출할 때 **어떤 문제를 백엔드가 막아야 하는지** 정리한다.

핵심은 모든 문제를 `rate limit` 하나로 해결하려 하지 않는 것이다.

```text
중복 데이터 방지 → UNIQUE / idempotency
재화 음수 방지 → Atomic Update
상태 경쟁 방지 → transaction / FOR UPDATE
너무 많은 요청 자체 완화 → rate limit
Docker 폭주 방지 → 실행 동시성 제한
```

각 문제에 맞는 도구를 쓴다.

---

## 1. 왜 필요한가

게임 API는 일반 CRUD보다 반복 호출 동기가 강하다.

예:

- 문제 제출 연타
- 상점 구매 연타
- 가챠 연타
- 출석 중복 시도
- 방 생성/입장 반복
- WebSocket 메시지 폭주
- 고양이 AI 대화 API 반복 호출

프론트 버튼을 잠그는 것만으로는 서버를 보호할 수 없다.

---

## 2. 출석

출석은 rate limit이 핵심 방어가 아니다.

최종 방어:

```text
UNIQUE(user_id, check_in_date)
+ 같은 transaction에서 100원 지급
```

같은 날 요청을 50번 보내도 데이터와 보상은 한 번만 성공해야 한다.

rate limit은 서버 부하 완화를 위한 추가 수단일 뿐이다.

---

## 3. 상점 구매

핵심 방어:

```sql
UPDATE users
SET balance = balance - :price
WHERE id = :user_id
  AND balance >= :price;
```

버튼을 여러 번 누르면 **각 구매가 독립된 정상 구매인지**가 중요하다.

사용자가 실제로 5개를 구매할 의도가 있는지, 동일 request 재전송인지 구분하려면 향후 idempotency key를 검토할 수 있다.

단순 rate limit만 걸면 동시성에 의한 잔액 오류 자체를 해결하지 못한다.

---

## 4. 가챠

가챠는 재화 차감 + 결과 지급이 같은 transaction이어야 한다.

위험:

```text
버튼 2회 클릭
→ 두 요청 모두 정상 처리
```

이게 기획상 2회 뽑기로 인정되는지, 네트워크 중복 요청으로 한 번만 인정해야 하는지 API 계약이 필요하다.

필요하면:

```text
client_request_id / idempotency key
```

같은 방법을 검토한다.

정확한 구조는 `29_idempotency_duplicate_request_policy.md`와 함께 본다.

---

## 5. 문제 제출

사용자는 학습 재시도를 무제한으로 할 수 있어도 짧은 시간에 수백 개 요청을 보내도록 둘 필요는 없다.

두 종류의 제한을 구분한다.

### 실행 동시성

Docker는 semaphore로 제한.

```text
PENDING은 많이 생길 수 있음
실제 컨테이너는 설정된 개수만 실행
```

### API 요청량

악의적인 제출로 PENDING row가 과도하게 쌓이면 별도 사용자별 요청 제한을 검토한다.

정확한 초당/분당 숫자는 지금 확정하지 않는다.

---

## 6. 로그인

인증이 구현되면 비밀번호 대입 공격을 고려한다.

후보 방어:

- IP/계정 기준 로그인 실패 횟수 제한
- 짧은 시간 반복 로그인에 429
- 로그에 실패 패턴 기록

하지만 계정 잠금 정책은 사용자를 실수로 막을 수 있으므로 별도 합의 없이 임의 구현하지 않는다.

---

## 7. 방 생성

사용자가 방을 무한 생성하면 ROOMS가 쌓일 수 있다.

검토 항목:

```text
사용자당 동시에 WAITING room을 몇 개까지 만들 수 있는가?
오래된 빈 방을 언제 정리할 것인가?
FINISHED room 보존기간은?
```

정확한 제한값은 기획/운영 정책이 필요하다.

---

## 8. 방 입장

방 입장은 rate limit보다:

```text
ROOMS FOR UPDATE
→ 상태/인원 확인
→ UNIQUE(room_id,user_id)
```

가 핵심이다.

동시에 마지막 한 자리를 여러 사용자가 노려도 정원을 넘기지 않아야 한다.

---

## 9. WebSocket 메시지

WebSocket 연결 후 클라이언트가 메시지를 무한 전송할 수 있다.

MVP에서 대부분의 상태 변경을 REST로 두면 공격 면적을 줄일 수 있다.

클라이언트 WebSocket 입력을 받게 된다면:

- 허용된 `type`만 처리
- payload validation
- 해당 room 참가자 여부 확인
- 필요 시 사용자별 메시지 빈도 제한

을 적용한다.

---

## 10. 고양이 AI 대화

외부 LLM API를 호출한다면 비용/지연 문제가 있으므로 일반 DB 조회보다 요청 제한 필요성이 높다.

검토:

```text
사용자별 동시 대화 요청 제한
한 메시지 최대 길이
외부 API timeout
실패 retry 횟수
```

정확한 숫자는 Gemini/LLM 사용 방식이 확정된 뒤 정한다.

---

## 11. HTTP 429

실제 요청량 제한을 적용한다면 일반적으로:

```http
429 Too Many Requests
```

를 사용할 수 있다.

응답 예시 후보:

```json
{
  "detail": "Too many requests. Please try again later."
}
```

프론트는 무한 자동 재시도하지 않는다.

---

## 12. Redis가 반드시 필요한가

아니다.

single worker MVP에서는 단순한 in-memory 제한으로 개발할 수도 있지만 서버 재시작 시 초기화되고 multi-worker에서는 공유되지 않는다.

정말 서비스 전체 기준 rate limit이 필요해지면 Redis 같은 공유 저장소를 검토한다.

현재 단계에서 단순히 "rate limit이 필요할 수도 있다"는 이유로 Redis를 먼저 넣지 않는다.

---

## 13. 로그

다음 이상 패턴은 운영 로그에 도움이 된다.

- 짧은 시간 대량 로그인 실패
- 같은 사용자 수십 번 가챠/구매 요청
- Docker submit 폭주
- 존재하지 않는 room/task 반복 요청
- 권한 없는 관리자 API 반복 접근

민감한 비밀번호/토큰/전체 코드는 로그에 남기지 않는다.

---

## 14. 테스트

- 출석 50회 동시 요청 → 출석/보상 1회
- 잔액보다 많은 동시 구매 → 잔액 음수 없음
- 마지막 방 자리 동시 입장 → 정원 초과 없음
- 제출 다량 요청 → Docker 실제 실행 수 제한
- 허용하지 않은 WebSocket type 거절
- rate limit 적용 기능은 기준 초과 시 429
- 제한 이후 정상 시간이 지나면 다시 요청 가능

---

# 결론

어뷰징 방어는 다음처럼 계층적으로 본다.

```text
데이터 무결성
→ DB 제약/transaction

중복 이벤트
→ idempotency

상태 경쟁
→ lock/Atomic Update

컴퓨팅 자원 폭주
→ semaphore/queue

과도한 요청 자체
→ rate limit
```

rate limit은 마지막 안전장치 중 하나이지 DB 동시성 설계를 대신하지 않는다.