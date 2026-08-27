# E. 인증·JWT 테스트 케이스

표기:

- **NOW**: 현재 모델/공통 코드로 확인 가능한 범위
- **AFTER**: 인증 구현 후 테스트
- **POLICY**: 로그인 방식·token 정책 확정 후 기대값 고정

현재 auth router 자체는 없으므로 대부분 AFTER다.

---

## E-T01. 회원가입 정상 — AFTER/POLICY

로컬 아이디/비밀번호 방식을 채택한다면:

**Then**
- 사용자 생성
- password 원문 저장 금지
- password_hash만 저장
- Response에 password/hash 없음

---

## E-T02. username 중복 — AFTER/POLICY

username UNIQUE를 채택한다면 동시에 같은 username으로 가입해도 사용자 row는 하나만 성공해야 한다.

DB UNIQUE를 최종 방어선으로 사용한다.

---

## E-T03. 입력 validation — AFTER

빈 username, 허용하지 않는 길이/형식, 빈 password 등을 확정 규칙에 맞춰 거절한다.

---

## E-T04. 정상 로그인 — AFTER

올바른 자격증명으로 로그인하면 인증 성공과 함께 token을 발급한다.

---

## E-T05. 잘못된 로그인 — AFTER

없는 username과 틀린 password를 지나치게 구체적으로 구분하지 않고 `401` 계열로 처리한다.

비밀번호 원문을 로그에 남기지 않는다.

---

## E-T06. 첫 로그인 자동 출석 — AFTER

오늘 첫 로그인 시:

```text
로그인 성공
→ ATTENDANCES 1개
→ balance +100
```

이 되어야 한다.

---

## E-T07. 같은 날 재로그인 — AFTER

같은 날 다시 로그인한다.

**Then**
- 로그인은 정상 성공
- attendance 추가 row 없음
- 100원 추가 지급 없음

UNIQUE 충돌이 로그인 실패로 번지면 안 된다.

---

## E-T08. 동시 로그인 자동 출석 — AFTER

같은 user로 동시에 여러 로그인 요청을 보낸다.

**Then** 하루 attendance 1개, 100원 지급 1회만 성공해야 한다.

---

## E-T09. 유효 JWT 보호 API — AFTER

정상 token으로 보호 endpoint 호출 시 current_user가 올바르게 식별되어야 한다.

---

## E-T10. token 없음/변조/만료 — AFTER/POLICY

각 경우 `401` 처리하고 보호 데이터 변경이 없어야 한다.

정확한 만료시간은 POLICY.

---

## E-T11. user_id 위조 방지 — AFTER

사용자 A가 Request body/path에 B의 UUID를 넣어도 최종 쓰기 API는 JWT A를 기준으로 처리하거나 요청을 거절해야 한다.

대상:

- 상점
- 가챠
- 하우징
- 학습 제출
- 출석
- 배틀
- 승급전
- 고양이 대화

---

## E-T12. `/me` — AFTER

유효 token이면 본인 정보만 반환하고 password/hash/token secret은 노출하지 않는다.

---

## E-T13. 401 vs 403 — AFTER

- 인증 자체 실패 → 401
- 인증 성공했지만 권한 없음 → 403

예: 일반 user의 관리자 endpoint 호출.

---

## E-T14. role guard — AFTER

일반 user는 관리자 master data 수정 불가, admin은 확정 권한 범위에서만 가능해야 한다.

---

## E-T15. refresh — AFTER/POLICY

refresh를 채택할 경우:

- 유효 refresh → 새 access
- 만료/변조 refresh → 거절
- 다른 사용자 token으로 변환 불가
- 저장 전략에 맞는 logout/revoke 동작

---

## E-T16. logout — AFTER/POLICY

stateless/access-only인지 refresh 기반인지에 따라 실제 기대 동작을 확정한 뒤 테스트한다.

---

## E-T17. WebSocket 인증 — AFTER

유효 JWT + 실제 room participant만 연결 가능해야 한다.

query의 user_id 문자열만으로 인증하지 않는다.

---

## E-T18. 비밀정보 로그 비노출 — AFTER

로그/예외/Response에서 다음이 노출되지 않는지 확인한다.

```text
password 원문
password_hash
JWT secret
전체 Authorization token
```

---

# E 완료 기준

```text
신뢰 가능한 사용자 식별
→ 자동 출석 연결
→ JWT 기반 ownership
→ 401/403
→ 비밀정보 보호
```

가 핵심이다.
