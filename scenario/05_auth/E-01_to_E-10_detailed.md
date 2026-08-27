# E-01 ~ E-10. 로그인·회원가입 상세 시나리오

이 문서는 인증 기능을 실제로 만들기 전에 필요한 사용자 흐름과 서버 검증을 정리한다.

> 현재 ERD의 `USERS`에는 비밀번호 hash나 소셜 로그인 식별자가 없다. 따라서 이 영역은 구현 전에 스키마 보완이 반드시 필요하다.

---

# E-01. 회원가입 화면 진입

## 목적
신규 사용자가 계정을 만들기 위해 필요한 입력 화면을 여는 단계다.

## 화면 후보
- username
- password
- password 확인

소셜 로그인을 선택하면 입력 필드는 달라질 수 있다.

## DB 변경
없다. 화면 진입 자체는 서버 상태를 바꾸지 않는다.

## 아직 결정할 것
- 아이디+비밀번호 방식인지
- Google 등 소셜 로그인인지
- 두 방식을 모두 지원하는지

---

# E-02. 정상 회원가입

## 로컬 로그인 방식일 경우 추천 흐름
```text
사용자가 username/password 입력
→ POST /auth/signup
→ 서버 입력 검증
→ username 중복 확인
→ password를 hash
→ USERS INSERT
→ COMMIT
→ 가입 성공 응답
```

## 가장 중요한 보안 원칙
비밀번호 원문을 DB에 저장하면 안 된다.

```text
password = "1234" 저장 ❌
password_hash = 안전한 hash 결과 저장 ✅
```

## ERD 변경 필요
현재 USERS에 최소한 `password_hash` 같은 컬럼이 필요하다.

## 초기값
가입 시 `balance`, `mileage`, `house_level`, `role`의 기본값도 기획에서 확정해야 한다.

---

# E-03. username 중복

## 상황
이미 `catlover`라는 username이 있는데 새 사용자가 같은 이름으로 가입한다.

## 해결
애플리케이션에서 먼저 확인할 수 있지만 최종 방어는 DB UNIQUE가 가장 강하다.

```text
USERS.username UNIQUE
```

## 처리
```text
INSERT 시도
→ UNIQUE 충돌
→ rollback
→ 409 Conflict
```

## 왜 DB UNIQUE가 필요한가
동시에 두 회원가입 요청이 오면 둘 다 사전 SELECT에서 `없음`을 볼 수 있다. DB UNIQUE가 마지막 방어벽이 된다.

---

# E-04. 잘못된 회원가입 입력

## 검사 후보
- username 빈 문자열
- 너무 짧거나 긴 username
- 허용하지 않는 문자
- password 최소 길이
- password와 확인값 불일치

## 역할 분담
password 확인값 비교는 프론트에서도 할 수 있지만 서버도 입력 규칙을 다시 검증해야 한다.

## Response
FastAPI/Pydantic validation을 활용해 422 또는 정책상 400을 반환할 수 있다.

## 테스트
경계값을 꼭 확인한다. 예를 들어 최소 길이가 확정되면 `최소-1`, `최소`, `최소+1`을 테스트한다.

---

# E-05. 정상 로그인

## 로컬 인증 기준 흐름
```text
username/password 제출
→ USERS에서 username 조회
→ 저장된 password_hash와 입력 password 검증
→ 성공
→ Access Token 발급
→ 프론트가 토큰 저장
→ 홈 이동
```

## JWT에 넣을 값
최소한 사용자 식별자와 만료시각을 포함할 수 있다. role이 권한 검사에 필요하면 claim으로 넣거나 매 요청 DB 조회 전략을 선택한다.

## 주의
JWT에는 password 같은 비밀정보를 넣지 않는다.

---

# E-06. 비밀번호 오류

## 상황
username은 맞지만 password가 틀렸다.

## 처리
```text
사용자 조회
→ hash 검증 실패
→ 401 Unauthorized
```

## 보안상 메시지
`해당 아이디는 존재하지만 비밀번호가 틀렸습니다`처럼 계정 존재 여부를 너무 자세히 노출하지 않고 `아이디 또는 비밀번호를 확인해주세요`로 통일할 수 있다.

## DB 변경
없음.

---

# E-07. Access Token 만료

## 상황
사용자가 로그인한 지 오래되어 access token의 만료 시간이 지났다.

## 서버
보호 API가 토큰 검증 중 만료를 발견하면 401을 반환한다.

## 선택지
### 단순 MVP
Access Token만 사용 → 만료되면 다시 로그인

### 일반적인 방식
짧은 Access Token + 긴 Refresh Token → access 재발급

## 추가 설계
Refresh Token을 안전하게 폐기/추적하려면 저장 위치와 로그아웃 정책이 필요하다.

## 아직 결정
토큰 만료시간은 임의로 정하지 않는다.

---

# E-08. 인증된 API에서 user_id 위조 방지

## 현재 임시 API의 문제
현재 여러 API는 body/path로 `user_id`를 받는다.

악의적 사용자가 다른 사람 UUID를 넣으면 다른 사용자 데이터에 접근할 위험이 있다.

## JWT 이후 추천
```text
Authorization: Bearer <token>
→ 서버가 token에서 현재 user_id 확인
→ body에서는 user_id를 받지 않음
```

예: 상점 구매 Request
```json
{
  "item_id": 5
}
```

누구의 balance를 차감할지는 JWT로 결정한다.

## 예외
관리자용 API처럼 다른 user_id를 명시적으로 다뤄야 하는 기능은 별도 권한 검사를 한다.

---

# E-09. 로그아웃

## Access Token만 사용하는 단순 JWT
프론트가 토큰을 삭제하면 이후 요청을 인증할 수 없게 된다.

## Refresh Token을 사용하는 경우
프론트에서 삭제하는 것만으로 충분한지, 서버에서도 refresh token을 무효화할지 정책이 필요하다.

## 화면
```text
로그아웃 클릭
→ 인증정보 제거
→ 로그인 화면 이동
```

## 테스트
로그아웃 후 기존 보호 API를 호출했을 때 인증 실패하는지 확인한다.

---

# E-10. role 권한 제한

## 목적
일반 학습자가 관리자 기능을 직접 API로 호출하지 못하게 한다.

## 흐름
```text
보호 API 호출
→ JWT 인증
→ 현재 사용자 role 확인
→ 허용 role인가?
  YES → 처리
  NO → 403 Forbidden
```

## 401과 403 차이
초보자 기준:
- `401`: 누구인지 인증이 안 됨
- `403`: 누군지는 알지만 이 기능을 쓸 권한이 없음

## 테스트
- 일반 user가 관리자 API 호출
- 관리자 정상 호출
- token 없이 호출
- 변조된 token

---

# E 영역에서 팀이 반드시 확정해야 할 것

1. 로컬 username/password 가입 여부
2. 소셜 로그인 도입 여부
3. `USERS.password_hash` 등 필요한 컬럼
4. username UNIQUE 여부(추천: UNIQUE)
5. username/password 입력 규칙
6. 가입 시 balance/mileage/house_level 기본값
7. role 기본값
8. Access Token 만료시간
9. Refresh Token 사용 여부와 만료시간
10. 토큰을 프론트 어디에 저장할지
11. 로그아웃 시 refresh 무효화 정책
12. 기존 API의 user_id를 JWT 기반으로 언제 전환할지
