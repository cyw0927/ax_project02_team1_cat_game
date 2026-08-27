# 인증·JWT 상세 흐름

이 문서는 회원가입/로그인/JWT가 실제 API 흐름에서 어떻게 연결되는지 정리한다.

현재 프로젝트는 인증이 아직 완전히 붙지 않았고 일부 API가 body/path로 `user_id`를 받는다. 이 문서는 **최종적으로 user_id를 토큰에서 가져오는 구조**로 옮길 때 필요한 공통 기준을 정리한다.

---

## 1. 회원가입

로컬 계정 방식을 채택한다면 최소 흐름은:

```text
username 입력
password 입력
→ 형식 검증
→ username 중복 확인
→ password hash 생성
→ USERS INSERT
→ 성공 응답
```

현재 USERS에는 password_hash가 없으므로 로컬 인증을 확정하면 migration이 필요하다.

소셜 로그인을 선택하면 필요한 컬럼과 흐름이 달라진다.

---

## 2. 비밀번호 저장

평문 password를 DB에 저장하지 않는다.

```text
사용자가 입력한 password
→ 안전한 password hashing
→ password_hash만 저장
```

로그에도 password를 남기지 않는다.

---

## 3. 로그인

```text
username/password 전달
→ user 조회
→ hash 검증
→ 성공 시 access token 발급
```

refresh token까지 사용할지는 팀 정책으로 확정한다.

정확한 만료시간 숫자는 임의로 고정하지 않는다.

---

## 4. JWT에 넣을 값

최소 후보:

```text
sub = user_id
role = 권한이 필요하면 포함 검토
exp = 만료시각
```

username, balance 같은 자주 바뀌는 값을 토큰의 진실 기준으로 사용하지 않는다.

예:

```text
JWT에 balance=1000
→ 사용자가 상점 구매
→ DB balance=800
→ 예전 token에는 여전히 1000
```

이런 값은 DB에서 읽는다.

---

## 5. 인증된 API 흐름

현재 임시:

```json
{
  "user_id": "uuid",
  "item_id": 5
}
```

최종 방향:

```text
Authorization: Bearer <token>
```

Body:

```json
{
  "item_id": 5
}
```

서버:

```text
JWT 검증
→ sub에서 user_id 추출
→ USERS 존재/상태 확인
→ 해당 user_id로 로직 수행
```

---

## 6. 왜 body의 user_id를 제거하나

사용자가 body를 바꿀 수 있기 때문이다.

```json
{"user_id":"다른사람UUID"}
```

를 보내 다른 사용자 자산을 수정할 수 있으면 안 된다.

따라서 자신의 출석/구매/가챠/하우징 변경은 token identity를 우선한다.

---

## 7. URL의 user_id가 필요한 경우

모든 user_id path가 나쁜 것은 아니다.

예:

```text
GET /users/{user_id}/house
```

처럼 다른 사용자의 공개 하우스를 보는 기능은 target user_id가 필요할 수 있다.

하지만 쓰기 API는:

```text
PATCH /users/{user_id}/house/...
```

보다 `/me/...` 또는 token identity 기반 검사가 더 명확할 수 있다.

최종 URL 스타일은 프론트와 합의한다.

---

## 8. 401과 403

개념적으로 구분한다.

```text
401 Unauthorized
= 인증 자체가 없거나 token이 유효하지 않음

403 Forbidden
= 로그인은 했지만 해당 행동 권한이 없음
```

예:

```text
token 만료 → 401
다른 사람 방을 비방장이 시작 → 403
```

상세 status 통일은 공통 오류 정책과 맞춘다.

---

## 9. role

USERS.role이 있으므로 관리자 기능이 생기면:

```text
일반 user
admin
```

등을 사용할 수 있다.

하지만 role 문자열 값은 팀에서 확정한다.

권한 검사는 프론트 메뉴 숨김만으로 끝내지 않고 서버에서도 수행한다.

---

## 10. WebSocket 인증

실시간 배틀도 사용자 식별이 필요하다.

WebSocket handshake 또는 연결 직후 token을 검증하고:

```text
JWT user_id
→ ROOM_PARTICIPANTS에 실제 참가자인지 확인
```

한다.

단순 query의 user_id만 믿지 않는다.

---

## 11. token 만료 중 게임 플레이

배틀/승급전 도중 token이 만료될 수 있다.

정해야 하는 것:

- 프론트가 refresh를 지원하는가
- WebSocket 장기 연결의 인증 만료를 어떻게 다룰 것인가
- API 재요청 시 로그인 화면으로 보낼 것인가

이 부분은 인증 방식 확정 후 프론트와 함께 결정한다.

---

## 12. 로그아웃

JWT가 완전 stateless라면 프론트에서 token을 삭제하는 방식이 가장 단순하다.

서버 강제 로그아웃/refresh token 폐기까지 필요하면 별도 저장 구조가 필요할 수 있다.

MVP 범위에서 어디까지 할지 정한다.

---

## 13. 민감정보 비노출

Response/로그에 다음을 보내지 않는다.

- password
- password_hash
- JWT secret
- DB password
- 전체 Authorization header

---

## 14. JWT 도입 시 한꺼번에 확인할 API

특히 다음 쓰기 API들은 body/path user_id 제거 또는 ownership 변경 영향이 크다.

```text
POST /attempts
POST /shop/buy
출석 check-in
가챠
하우징 배치/이동/삭제
승급전 시작/저장
배틀 참가/Ready
```

API 하나씩 제각각 인증 방식을 섞기보다 전환 목록을 만들어 같이 수정한다.

---

## 15. 테스트

- 정상 회원가입
- username 중복
- 정상 로그인
- 틀린 password
- token 없이 보호 API
- 잘못된 token
- 만료 token
- token user_id와 body 위조 user_id 충돌
- 일반 user가 admin API 호출
- 다른 사용자 자산 수정 시도
- WebSocket 비참가자 연결

---

# 구현 전 확정사항

```text
[ ] 로컬 로그인인가, 소셜 로그인인가
[ ] USERS에 필요한 인증 컬럼
[ ] username UNIQUE/규칙
[ ] access token 만료 정책
[ ] refresh token 사용 여부
[ ] role 값
[ ] 로그아웃 수준
[ ] 프론트 token 보관 방식
```

인증은 단순히 로그인 화면을 만드는 기능이 아니라 **서버가 '누가 이 요청을 했는지' 신뢰할 수 있게 만드는 기반 기능**이다.