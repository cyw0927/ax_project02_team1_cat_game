# 학습용 고양이 게임 API 명세서

## 1. 문서 목적

이 문서는 학습용 고양이 게임의 Backend API 규칙과 Frontend 연동 방법을 정의한다.

Backend와 Frontend는 이 문서를 공통 계약으로 사용한다. API 구현이 변경되면 코드와 함께 이 문서도 수정한다.

---

## 2. 기본 정보

### 2.1 개발 서버 주소

```text
http://127.0.0.1:8000
```

### 2.2 API 문서

```text
Swagger UI: http://127.0.0.1:8000/docs
OpenAPI JSON: http://127.0.0.1:8000/openapi.json
```

### 2.3 데이터 형식

- 요청과 응답 본문은 JSON을 사용한다.
- JSON 필드명은 `snake_case`를 사용한다.
- UUID는 문자열로 전달한다.
- 날짜와 시간은 ISO 8601 문자열로 전달한다.
- 날짜만 필요한 값은 `YYYY-MM-DD` 형식을 사용한다.
- 재화, 마일리지, 수량, 점수는 정수로 전달한다.
- 상태 및 등급 값은 대문자 문자열을 사용한다.

예시:

```json
{
  "user_id": "00000000-0000-0000-0000-000000000001",
  "status": "PENDING",
  "soft_balance": 1000,
  "created_at": "2026-08-30T15:30:00+09:00"
}
```
### 2.4 실행 환경변수

Backend 실행 환경은 다음 환경변수를 사용한다.

| 환경변수 | 공개 여부 | 설명 | 개발 환경 예시 |
|---|---|---|---|
| `APP_ENV` | 공개 가능 | 현재 실행 환경 | `development` |
| `APP_HOST` | 공개 가능 | Backend 서버 실행 주소 | `127.0.0.1` |
| `APP_PORT` | 공개 가능 | Backend 서버 실행 포트 | `8000` |
| `APP_TIMEZONE` | 공개 가능 | 출석 및 일일 기능의 서비스 기준 timezone | `Asia/Seoul` |
| `CORS_ORIGINS` | 공개 가능 | Backend 접근이 허용된 Frontend 주소 목록 | `http://localhost:5500,http://127.0.0.1:5500` |
| `DATABASE_URL` | 비공개 | PostgreSQL 접속 정보 | 명세서에 작성하지 않음 |
| `SANDBOX_IMAGE` | 운영 설정 | 코드 채점용 Docker 이미지 | 채점 기능 구현 시 확정 |
| `SANDBOX_TIMEOUT_SECONDS` | 운영 설정 | 코드 실행 제한 시간 | 채점 기능 구현 시 확정 |
| `SANDBOX_MEMORY` | 운영 설정 | Docker 메모리 제한 | `128m` |
| `SANDBOX_CPUS` | 운영 설정 | Docker CPU 제한 | `0.5` |
| `SANDBOX_OUTPUT_BYTES` | 운영 설정 | 채점 결과 출력 크기 제한 | 채점 기능 구현 시 확정 |
| `SANDBOX_MAX_CONCURRENCY` | 운영 설정 | 동시에 실행할 수 있는 채점 수 | `3` |

실제 비밀번호와 API 키는 `server/.env`에만 저장하고 Git에 포함하지 않는다.

팀원이 사용할 수 있는 공개 예시는 `server/.env.example`에 작성한다.

### 2.5 CORS 정책

개발 환경에서 Backend 접근이 허용된 Frontend 주소는 다음과 같다.

http://localhost:5500
http://127.0.0.1:5500

Backend는 `CORS_ORIGINS` 환경변수에 등록된 주소만 브라우저 접근을 허용한다.

여러 주소는 쉼표로 구분하며 주소 사이에 공백을 넣지 않는다.

CORS_ORIGINS=http://localhost:5500,http://127.0.0.1:5500

주소 끝에는 `/`를 붙이지 않는다.

잘못된 예시:
http://localhost:5500/


올바른 예시:
http://localhost:5500


Frontend 개발 서버의 포트가 변경되면 Backend의 `CORS_ORIGINS`에도 새로운 주소를 추가해야 한다.

운영 환경에서는 실제 배포된 Frontend 주소만 허용하고 `*` 전체 허용은 사용하지 않는다.

### 2.6 Frontend 연동 주소

개발 환경의 기본 Backend 주소는 다음과 같다.

http://127.0.0.1:8000

Frontend는 API 주소를 화면 코드에 여러 번 직접 작성하지 않고 별도의 Frontend 환경변수로 관리한다.

Frontend 환경변수 이름은 Frontend 기술 스택이 확정되면 정한다.

예시:

VITE_API_BASE_URL=http://127.0.0.1:8000

Frontend 개발 서버 주소나 포트가 변경되면 Backend 담당자에게 전달하여 CORS 허용 주소를 함께 수정한다.
---

## 3. Backend와 Frontend의 공통 원칙

### 3.1 Backend 책임

Backend는 다음 값을 최종적으로 검증하고 결정한다.

- 사용자 권한
- 상품 가격
- 사용자 보유 재화
- 보상 지급량
- 문제 정답 여부
- 숙련도 변경량
- 가챠 결과
- 아이템 및 고양이 지급
- 배틀 점수와 승패
- 랭킹 점수와 승급 결과
- 중복 요청 및 중복 보상 여부

Frontend에서 계산한 결과를 그대로 신뢰하지 않는다.

### 3.2 Frontend 책임

Frontend는 다음 작업을 담당한다.

- 사용자 입력값 수집
- API 요청 전송
- 로딩 상태 표시
- Backend 응답을 화면에 표시
- 오류 메시지 표시
- 재시도가 가능한 오류 처리
- 버튼 중복 클릭 방지
- API 처리 완료 후 관련 화면 데이터 갱신

### 3.3 공개하지 않는 데이터

다음 정보는 Frontend에 전달하지 않는다.

- 문제의 비공개 테스트 케이스
- 정답 코드
- 실제 비밀번호
- API 키
- 내부 오류 상세 내용
- 다른 사용자의 비공개 데이터
- AI 시스템 프롬프트

---

## 4. 인증 및 현재 사용자 식별

현재는 회원가입, 로그인 및 JWT가 구현되기 전의 개발 단계다.

개발 및 테스트 환경에서는 다음 헤더로 현재 사용자를 임시 식별한다.

```http
X-User-ID: 00000000-0000-0000-0000-000000000001
```

### 4.1 적용 환경

- 허용: `APP_ENV=development`, `APP_ENV=test`
- 차단: 그 외 모든 환경

운영 환경에서는 `X-User-ID`를 보내도 현재 사용자로 인정하지 않고 `401 AUTHENTICATION_REQUIRED`를 반환한다.

이 헤더는 인증 수단이 아니며, 개발 중 `DEV-001` 사용자로 API를 연결하기 위한 임시 식별 장치다.

### 4.2 Backend 처리

1. 실행 환경이 개발 또는 테스트인지 확인한다.
2. `X-User-ID` 헤더가 있는지 확인한다.
3. 헤더 값을 UUID로 변환한다.
4. 해당 UUID의 사용자가 DB에 존재하는지 확인한다.
5. 확인된 ORM `User` 객체를 현재 요청의 `current_user`로 제공한다.
6. 보호 API는 요청 Body나 Path의 사용자 ID보다 `current_user.id`를 우선한다.

현재 사용자 식별 로직은 공통 dependency로 분리한다. JWT 도입 후에는 API별 로직을 다시 작성하지 않고 dependency 내부를 Bearer Token 검증 방식으로 교체한다.

### 4.3 Frontend 처리

1. 개발 환경에서만 현재 개발용 사용자의 UUID를 `X-User-ID` 헤더로 전달한다.
2. UUID를 여러 화면에 직접 작성하지 않고 공통 API client 설정에서 관리한다.
3. `401` 응답을 받으면 현재 사용자 설정을 확인하고 사용자 데이터를 화면에 반영하지 않는다.
4. 운영 build에는 개발용 사용자 UUID를 포함하지 않는다.
5. JWT가 도입되면 `X-User-ID`를 제거하고 `Authorization: Bearer <token>`으로 전환한다.

### 4.4 현재 사용자 조회

```http
GET /me
X-User-ID: 00000000-0000-0000-0000-000000000001
```

성공 상태 코드는 `200 OK`이며 응답은 `UserResponse`를 사용한다.

```json
{
  "id": "00000000-0000-0000-0000-000000000001",
  "external_student_id": "DEV-001",
  "username": "개발용 학습자",
  "role": "USER",
  "soft_balance": 1000,
  "hard_balance": 100,
  "mileage": 0,
  "house_level": 1,
  "wallpaper_item_id": null,
  "floor_item_id": null,
  "created_at": "2026-08-30T12:00:00+09:00"
}
```

### 4.5 식별 실패 응답

- 헤더 누락
  - 상태: `401 Unauthorized`
  - 코드: `CURRENT_USER_ID_REQUIRED`
- UUID 형식 오류
  - 상태: `401 Unauthorized`
  - 코드: `INVALID_CURRENT_USER_ID`
- DB에 사용자가 없음
  - 상태: `401 Unauthorized`
  - 코드: `CURRENT_USER_NOT_FOUND`
- 운영 환경에서 임시 헤더 사용
  - 상태: `401 Unauthorized`
  - 코드: `AUTHENTICATION_REQUIRED`

공통 오류 형식 예시:

```json
{
  "error": {
    "code": "CURRENT_USER_ID_REQUIRED",
    "message": "X-User-ID 헤더가 필요합니다.",
    "details": []
  }
}
```

### 4.6 JWT 전환 원칙

```text
현재: X-User-ID → DB User 조회
향후: Authorization Bearer Token → JWT sub → DB User 조회
```

사용자 재화, 역할 등 변경 가능한 값은 토큰이나 Frontend 값을 신뢰하지 않고 DB에서 조회한다.

역할별 권한, 토큰 만료, 재인증 및 로그아웃 정책은 후속 인증 단계에서 확정한다.

### 4.7 역할별 권한 검사

현재 지원 역할은 다음과 같다.

| 역할 | 의미 | 기본 허용 범위 |
| --- | --- | --- |
| `USER` | 일반 학습자 | 본인 학습, 출석, 재화 및 게임 기능 |
| `ADMIN` | 관리자 | 일반 기능 및 향후 관리자 전용 기능 |

Backend는 endpoint가 허용하는 역할 목록을 공통 role guard에 선언한다.

```text
현재 사용자 식별
→ DB의 최신 role 확인
→ endpoint 허용 역할과 비교
→ 허용 시 처리, 미허용 시 403
```

역할은 `X-User-ID`, 향후 JWT claim 또는 Frontend 입력값을 그대로 신뢰하지 않고 DB의 `users.role`을 기준으로 한다.

`GET /me`는 `USER`와 `ADMIN`을 허용한다. 정의되지 않은 역할은 `403 INSUFFICIENT_ROLE`을 반환한다.

관리자 전용 endpoint는 향후 다음과 같이 `ADMIN`만 허용한다.

```text
require_roles("ADMIN")
```

Frontend에서 관리자 메뉴를 숨기는 것은 편의 기능일 뿐이며, 실제 권한 차단은 항상 Backend에서 수행한다.

#### 401과 403 구분

- `401 Unauthorized`: 현재 사용자를 식별할 수 없음
- `403 Forbidden`: 사용자는 식별됐지만 endpoint에 필요한 역할이 없음

권한 부족 응답:

```json
{
  "error": {
    "code": "INSUFFICIENT_ROLE",
    "message": "이 작업을 수행할 권한이 없습니다.",
    "details": []
  }
}
```

Frontend는 `403`을 받으면 재로그인을 반복하지 않고 권한 부족 안내를 표시한다.

---

## 5. 공통 응답 규칙

### 5.1 성공 응답

각 API는 해당 기능에 필요한 데이터만 응답한다. DB 컬럼 전체를 그대로 노출하지 않는다.

예시:

```json
{
  "id": "00000000-0000-0000-0000-000000000001",
  "username": "개발용 사용자"
}
```

### 5.2 간단한 처리 완료 응답

```json
{
  "message": "처리가 완료되었습니다."
}
```

### 5.3 공통 오류 응답

모든 HTTP API 오류는 다음과 같은 공통 JSON 구조로 응답한다.

```json
{
  "error": {
    "code": "NOT_FOUND",
    "message": "요청한 데이터를 찾을 수 없습니다.",
    "details": []
  }
}
```

| 필드 | 타입 | nullable | 설명 |
|---|---|---|---|
| `error` | object | 아니요 | 오류 정보 |
| `error.code` | string | 아니요 | Frontend가 오류를 구분할 때 사용하는 고정 코드 |
| `error.message` | string | 아니요 | 사용자에게 표시할 수 있는 오류 설명 |
| `error.details` | array | 아니요 | 필드별 검증 오류 목록이며, 세부 오류가 없으면 빈 배열 |
| `error.details[].field` | string | 예 | 오류가 발생한 요청 필드 |
| `error.details[].message` | string | 아니요 | 해당 필드의 오류 설명 |
| `error.details[].type` | string | 예 | Pydantic 검증 오류 유형 |

### 5.4 요청값 검증 오류 예시

요청 경로, Query Parameter 또는 Request Body가 스키마와 맞지 않으면 `422 Unprocessable Entity`를 응답한다.

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "요청값이 올바르지 않습니다.",
    "details": [
      {
        "field": "path.user_id",
        "message": "Input should be a valid UUID",
        "type": "uuid_parsing"
      }
    ]
  }
}
```

Frontend는 `details`를 사용하여 오류가 발생한 입력 필드에 안내 문구를 표시할 수 있다.

### 5.5 공통 HTTP 오류 코드

| HTTP 상태 | 오류 코드 | 의미 | Frontend 처리 |
|---|---|---|---|
| `400 Bad Request` | `BAD_REQUEST` | 요청 내용 또는 처리 조건이 올바르지 않음 | 요청 내용을 확인하고 안내 메시지를 표시한다. |
| `401 Unauthorized` | `UNAUTHORIZED` | 사용자 인증이 필요하거나 유효하지 않음 | 로그인 또는 사용자 인증을 다시 요청한다. |
| `403 Forbidden` | `FORBIDDEN` | 해당 기능이나 데이터에 접근할 권한이 없음 | 접근 권한이 없음을 표시한다. |
| `404 Not Found` | `NOT_FOUND` | 요청한 API 또는 데이터를 찾을 수 없음 | 데이터가 없음을 표시하거나 이전 화면으로 이동한다. |
| `405 Method Not Allowed` | `METHOD_NOT_ALLOWED` | 지원하지 않는 HTTP 메서드 사용 | Frontend의 요청 메서드를 점검한다. |
| `409 Conflict` | `CONFLICT` | 중복 요청 또는 현재 데이터 상태와 충돌 | 최신 데이터를 다시 조회한 후 화면을 갱신한다. |
| `422 Unprocessable Entity` | `VALIDATION_ERROR` | Path, Query 또는 Body 검증 실패 | `details`를 이용해 잘못된 입력 필드를 표시한다. |
| `500 Internal Server Error` | `INTERNAL_SERVER_ERROR` | 서버 내부 오류 | 잠시 후 재시도하도록 안내한다. |

정의되지 않은 HTTP 오류에는 `HTTP_ERROR` 코드가 사용될 수 있다.

### 5.6 Frontend 오류 처리 원칙

- Frontend는 변경될 수 있는 `message` 문자열이 아니라 고정된 `error.code`를 기준으로 분기한다.
- `message`는 사용자 안내 문구로 사용할 수 있다.
- `details`가 비어 있지 않으면 해당 입력 필드에 검증 오류를 표시한다.
- `401` 응답을 받으면 현재 사용자 식별 또는 로그인 상태를 다시 확인한다.
- `403` 응답을 받으면 권한이 필요한 기능을 실행하지 않는다.
- `409` 응답을 받으면 중복 요청 여부를 확인하고 관련 데이터를 다시 조회한다.
- `422` 응답을 받으면 잘못된 입력 필드와 요청 형식을 확인한다.
- `500` 응답에는 내부 예외, SQL, 파일 경로 등의 상세 정보가 포함되지 않는다.
- 요청 처리 중에는 버튼 중복 클릭을 막고, 요청 완료 후 로딩 상태를 해제한다.



---

## 6. 비동기 채점 상태

학습, 일일 미션, 배틀, 랭킹전의 코드 제출은 공통 `TaskAttempt`를 사용한다.

| 상태 | 의미 | Frontend 처리 |
|---|---|---|
| `PENDING` | 제출 저장 및 채점 대기 | 채점 중 화면을 표시한다. |
| `RUNNING` | 채점 진행 중 | 로딩 상태를 유지한다. |
| `SUCCESS` | 채점 완료 | 정답 여부와 결과를 표시한다. |
| `FAILED` | 채점 처리 실패 | 오류 메시지와 재시도 방법을 표시한다. |

상태 이름은 실제 채점 기능 구현 시 최종 확정한다.

Frontend는 `PENDING` 또는 `RUNNING` 상태일 때 결과 조회 API를 일정 간격으로 호출한다. 호출 간격과 최대 대기 시간은 채점 기능 구현 시 정한다.

---

## 7. API별 작성 양식

새로운 API를 구현할 때마다 아래 양식을 복사하여 해당 기능 항목에 추가한다.

### `[HTTP 메서드] /api/path`

#### 기능

이 API가 수행하는 기능을 작성한다.

#### 연결 화면

이 API를 사용하는 Frontend 화면을 작성한다.

#### 인증 및 권한

- 인증 필요 여부:
- 허용 역할:
- 본인 데이터 확인 여부:

#### Backend 처리

1. 요청값을 검증한다.
2. 사용자와 권한을 확인한다.
3. 기능에 필요한 처리를 수행한다.
4. 처리 결과를 DB에 저장한다.
5. 응답 데이터를 반환한다.

#### Frontend 처리

1. 사용자 입력값을 수집한다.
2. API 요청을 보낸다.
3. 요청 중에는 로딩 상태를 표시한다.
4. 성공하면 응답 데이터를 화면에 반영한다.
5. 실패하면 오류 메시지와 재시도 방법을 표시한다.

#### Path Parameters

| 이름 | 타입 | 필수 | 설명 |
|---|---|---|---|
| 없음 |  |  |  |

#### Query Parameters

| 이름 | 타입 | 필수 | 기본값 | 설명 |
|---|---|---|---|---|
| 없음 |  |  |  |  |

#### Request Body

```json
{}
```

| 필드 | 타입 | 필수 | 설명 |
|---|---|---|---|
| 없음 |  |  |  |

#### 성공 응답

- 상태 코드: `200 OK`

```json
{}
```

| 필드 | 타입 | nullable | 설명 |
|---|---|---|---|
| 없음 |  |  |  |

#### 오류 응답

| 상태 코드 | 오류 코드 | 발생 조건 | Frontend 처리 |
|---|---|---|---|
| `400` | 작성 예정 | 잘못된 요청 | 입력 내용을 확인한다. |
| `401` | 작성 예정 | 인증 실패 | 로그인 또는 인증을 다시 요청한다. |
| `403` | 작성 예정 | 권한 없음 | 접근할 수 없음을 표시한다. |
| `404` | 작성 예정 | 데이터 없음 | 데이터가 없음을 표시한다. |
| `409` | 작성 예정 | 중복 또는 상태 충돌 | 최신 데이터를 다시 조회한다. |
| `422` | 작성 예정 | 입력값 검증 실패 | 잘못된 입력 필드를 표시한다. |
| `500` | 작성 예정 | 서버 내부 오류 | 잠시 후 재시도하도록 안내한다. |

#### 화면 갱신

API 성공 후 다시 조회해야 하는 데이터와 화면을 작성한다.

#### Frontend 주의사항

중복 클릭 방지, 로딩 표시, 빈 데이터 처리 등의 주의사항을 작성한다.

---

## 8. 사용자 및 출석 API

상태: 진행 중

완료된 API:

- `GET /me` 현재 사용자 조회
- `GET /me/attendance/today` 오늘 출석 여부 조회
- `POST /me/attendance/check-in` 현재 사용자 출석 체크
- `GET /users/{user_id}` 사용자 상세 조회
- `GET /users/external-student-id/availability` 외부 학생 ID 중복 검사

작성 예정 API:

- 사용자 생성
- 일일 미션 완료 처리(오늘 배정 문제 집합과 올클리어 판정 정책 확정 후 작성)

일일 미션 완료 상태는 현재 ERD의
`ATTENDANCES.daily_quest_completed`에 저장한다. 20개 미만 테이블 제약을
지키기 위해 별도 일일 미션 테이블을 추가하지 않고, 오늘 배정된 문제 ID
스냅샷은 같은 출석 row의 `daily_task_ids` JSONB 배열에 저장한다. 채점 로직은
이 배열에 포함된 문제를 모두 맞혔는지 확인한 뒤 같은 transaction에서 멱등
상태 전이를 호출한다. 문제 0개인 날은 자동 완료하지 않는다.

Frontend가 완료를 직접 선언하는 API는 제공하지 않는다. 문제 수를 임의로
가정하거나 실제 제출된 문제만을 전체 문제로 간주하지 않는다. 문제 선정
규칙과 보상 수치가 확정되면 채점 완료 흐름에서 자동으로 연결한다.

오늘 문제 선정 규칙은 다음과 같다.

- `TASKS.is_active = true`인 문제만 후보로 사용한다.
- 사용자 숙련도가 낮은 개념을 먼저 선택한다.
- 숙련도 기록이 없는 개념은 레벨 0으로 취급한다.
- 동률이면 `concept_id`, `task_id` 순서로 정렬해 결과를 고정한다.
- 최대 3개를 선택하며 출석 생성 시 `daily_task_ids`에 문자열 UUID 배열로 저장한다.
- 저장 이후 문제 활성 상태나 숙련도가 바뀌어도 당일 배정 스냅샷은 바꾸지 않는다.

### `GET /me/attendance/today`

#### 기능

현재 사용자가 서비스 기준 오늘 날짜에 출석했는지 조회한다.

이 API는 출석 기록과 재화를 변경하지 않는다.

#### 연결 화면

- 홈 화면의 오늘 출석 상태
- 일일 미션 진입 화면
- 출석 완료 표시 및 연속 출석 일수

#### 인증 및 권한

- 현재 식별 방식: 개발·테스트 환경의 `X-User-ID`
- 현재 허용 역할: `USER`, `ADMIN`
- 운영 환경: 향후 JWT 인증으로 전환

#### Backend 처리

1. 공통 현재 사용자 dependency로 사용자를 식별한다.
2. 서버 현재 시각을 `APP_TIMEZONE`으로 변환해 서비스 기준 날짜를 계산한다.
3. `(current_user.id, service_today)`에 해당하는 출석 기록을 조회한다.
4. 기록이 없으면 `checked_in_today: false`, `attendance: null`을 반환한다.
5. 기록이 있으면 `checked_in_today: true`와 출석 상세를 반환한다.
6. 클라이언트가 보내는 날짜나 기기 시간을 출석 판정에 사용하지 않는다.

#### Frontend 처리

1. 개발 환경에서는 공통 API client가 `X-User-ID` 헤더를 전달한다.
2. 화면 진입 또는 로그인 후 오늘 출석 상태가 필요할 때 호출한다.
3. `checked_in_today`가 `false`이면 미출석 상태를 표시한다.
4. `checked_in_today`가 `true`이면 `attendance.streak_count`와 일일 미션 완료 여부를 화면에 반영한다.
5. `attendance`가 `null`일 수 있으므로 필드에 바로 접근하지 않는다.
6. Frontend 날짜와 Backend 응답 날짜가 달라도 Backend 응답을 기준으로 한다.
7. `401`은 현재 사용자 식별 실패, `403`은 역할 부족으로 처리한다.

#### HTTP 요청

```http
GET /me/attendance/today
X-User-ID: 00000000-0000-0000-0000-000000000001
```

#### Query Parameters

- 없음

#### Request Body

- 요청 본문을 사용하지 않는다.

#### 미출석 응답

- 상태 코드: `200 OK`

```json
{
  "checked_in_today": false,
  "attendance": null
}
```

#### 출석 완료 응답

- 상태 코드: `200 OK`

```json
{
  "checked_in_today": true,
  "attendance": {
    "id": "10000000-0000-0000-0000-000000000001",
    "user_id": "00000000-0000-0000-0000-000000000001",
    "check_in_date": "2026-08-31",
    "streak_count": 3,
    "daily_quest_completed": false
  }
}
```

#### 성공 응답 필드

- `checked_in_today`
  - 타입: boolean
  - 설명: 서비스 기준 오늘 출석 기록의 존재 여부
- `attendance`
  - 타입: AttendanceResponse 또는 null
  - 설명: 오늘 출석 상세이며 미출석이면 `null`

#### 오류 응답

- `401 Unauthorized`
  - 발생 조건: 현재 사용자 헤더 누락, 잘못된 UUID, 미등록 사용자 또는 운영 환경의 임시 헤더 사용
  - Frontend 처리: 현재 사용자 설정 또는 인증 상태 확인
- `403 Forbidden`
  - 오류 코드: `INSUFFICIENT_ROLE`
  - 발생 조건: 현재 사용자의 역할이 허용 목록에 없음
  - Frontend 처리: 권한 부족 안내
- `500 Internal Server Error`
  - 발생 조건: 예상하지 못한 서버 또는 DB 오류
  - Frontend 처리: 미출석으로 간주하지 않고 오류와 재시도 UI 표시

#### 서비스 날짜 정책

- 환경변수: `APP_TIMEZONE`
- 현재 기본값: `Asia/Seoul`
- 형식: IANA timezone 이름
- 날짜 계산: timezone-aware 서버 시각을 설정 timezone으로 변환 후 날짜 추출
- 서버 OS timezone과 클라이언트 기기 날짜는 판정 기준으로 사용하지 않음

`APP_TIMEZONE`을 변경하면 출석과 향후 일일 제한 기능이 동일한 설정을 사용해야 한다.

### `POST /me/attendance/check-in`

#### 기능

현재 사용자의 오늘 출석 기록을 만들고 일반 재화 100을 지급한다.

#### 인증 및 권한

- 현재 식별 방식: 개발·테스트 환경의 `X-User-ID`
- 현재 허용 역할: `USER`, `ADMIN`
- 요청 Body나 Path에서 사용자 ID를 받지 않음

#### Backend 처리

1. 공통 현재 사용자 및 역할 dependency를 통과한다.
2. `APP_TIMEZONE` 기준 오늘과 어제 날짜를 계산한다.
3. 가장 최근 과거 출석을 조회한다.
4. 최근 출석이 어제이면 기존 `streak_count + 1`, 아니면 1로 계산한다.
5. 활성 문제 중 취약 개념 우선으로 최대 3개를 선정해 `daily_task_ids`에 저장하고, 오늘 출석을 `daily_quest_completed: false`로 생성한다.
6. DB의 `(user_id, check_in_date)` 고유 제약으로 같은 날 중복 출석을 차단한다.
7. 출석 INSERT와 `soft_balance + 100`을 같은 transaction에서 처리한다.
8. 성공하면 출석 상세, 지급량 및 최신 일반 재화를 반환한다.

#### Frontend 처리

1. 개발 환경에서는 공통 API client가 `X-User-ID`를 전달한다.
2. 출석 버튼 또는 로그인 연동 흐름에서 한 번 호출한다.
3. `201` 응답의 `attendance`와 `current_soft_balance`로 화면을 갱신한다.
4. `reward_amount`를 Frontend에서 다시 계산하지 않는다.
5. `409`이면 이미 출석한 상태로 안내하고 재화를 임의로 증가시키지 않는다.
6. 요청 중 버튼 중복 클릭을 막되 Backend의 DB 고유 제약을 최종 방어로 사용한다.

#### HTTP 요청

```http
POST /me/attendance/check-in
X-User-ID: 00000000-0000-0000-0000-000000000001
```

#### Request Body

- 요청 본문을 사용하지 않는다.

#### 성공 응답

- 상태 코드: `201 Created`

```json
{
  "attendance": {
    "id": "10000000-0000-0000-0000-000000000001",
    "user_id": "00000000-0000-0000-0000-000000000001",
    "check_in_date": "2026-08-31",
    "streak_count": 3,
    "daily_quest_completed": false
  },
  "reward_amount": 100,
  "current_soft_balance": 1100
}
```

#### 성공 응답 필드

- `attendance`
  - 타입: AttendanceResponse
  - 설명: 새로 생성된 오늘 출석 기록
- `reward_amount`
  - 타입: integer
  - 설명: 이번 출석으로 지급된 일반 재화
- `current_soft_balance`
  - 타입: integer
  - 설명: 보상 지급 후 사용자의 일반 재화 잔액

#### 중복 출석 응답

- 상태 코드: `409 Conflict`
- 오류 코드: `ATTENDANCE_ALREADY_CHECKED_IN`

```json
{
  "error": {
    "code": "ATTENDANCE_ALREADY_CHECKED_IN",
    "message": "오늘 출석이 이미 완료되었습니다.",
    "details": []
  }
}
```

#### 중복 출석 및 보상 방지

중복 방지의 최종 기준은 애플리케이션의 사전 조회가 아니라 DB의 다음 고유 제약이다.

```text
UNIQUE(user_id, check_in_date)
```

처리 순서는 다음과 같다.

```text
Attendance INSERT 및 flush
→ 고유 제약 통과
→ soft_balance + 100
→ commit
```

- 중복 INSERT가 flush에서 실패하면 즉시 rollback하고 `409 ATTENDANCE_ALREADY_CHECKED_IN`을 반환한다.
- 중복이 확인된 요청에서는 재화 UPDATE를 실행하지 않는다.
- 보상 UPDATE 또는 commit이 실패하면 transaction 전체를 rollback한다.
- 출석만 저장되고 보상은 지급되지 않는 부분 성공을 허용하지 않는다.
- Frontend의 버튼 비활성화는 UX 보조 수단이며 중복 방지의 최종 수단이 아니다.
- 여러 탭이나 기기의 요청도 동일한 고유 제약과 transaction을 사용한다.

같은 날짜의 두 번째 수동 출석 요청은 현재 `409` 정책을 사용한다. 향후 로그인 자동 출석에서는 이 충돌을 로그인 실패로 전파하지 않고 이미 출석한 정상 no-op으로 변환해야 한다.

#### 기타 오류 응답

- `401 Unauthorized`: 현재 사용자 식별 실패
- `403 Forbidden`: 허용되지 않은 역할
- `500 Internal Server Error`: 출석 또는 보상 transaction 처리 실패

#### 연속 출석 계산 정책

- 과거 출석 기록이 없으면 오늘 `streak_count`는 1이다.
- 가장 최근 과거 출석이 서비스 기준 어제이면 이전 `streak_count + 1`이다.
- 가장 최근 과거 출석이 이틀 이상 전이면 오늘 `streak_count`는 1로 초기화된다.
- 어제 날짜는 문자열이나 월 내부 숫자 비교가 아니라 날짜에서 하루를 빼서 계산한다.
- 따라서 월말, 연말 및 윤년의 2월 29일 경계에서도 같은 규칙을 적용한다.
- 추가 milestone 보상은 현재 정책에 포함하지 않는다.

Frontend는 연속 출석 일수를 자체 계산하지 않고 Backend 응답의 `attendance.streak_count`를 표시한다.

#### 기존 endpoint 호환 정책

기존 `POST /users/{user_id}/attendance/check-in`은 현재 코드와 개발 도구의 호환을 위해 남겨두지만 OpenAPI에서 deprecated로 표시한다.

Frontend 신규 코드는 반드시 `POST /me/attendance/check-in`을 사용한다. JWT 도입 후에도 URL과 Request Body는 유지하고 현재 사용자 dependency만 교체한다.

### `GET /users/external-student-id/availability`

#### 기능

사용자 생성 전에 외부 학생 ID가 이미 등록되어 있는지 확인한다.

중복 여부는 `users.external_student_id`의 고유 제약과 동일하게 대소문자를 구분하여 판정한다.

#### 연결 화면

- 회원가입 또는 사용자 등록 화면
- 외부 학생 ID 입력 필드의 중복 확인 상태

#### 인증 및 권한

- 현재 인증 필요 여부: 없음
- 현재 허용 역할: 모든 사용자
- 남용 방지: 인증 및 요청 횟수 제한 도입 시 함께 적용 예정

#### Backend 처리

1. Query Parameter의 `external_student_id`가 1자 이상 100자 이하이며 공백만으로 구성되지 않았는지 검증한다.
2. 값의 앞뒤 공백을 제거한다.
3. 정규화한 값과 정확히 일치하는 `users.external_student_id`를 조회한다.
4. 일치하는 사용자가 없으면 `is_available: true`, 있으면 `is_available: false`를 반환한다.
5. 중복인 경우에도 정상적인 조회 결과이므로 `409`가 아닌 `200`을 반환한다.
6. 이 API는 사전 확인 용도이며, 실제 사용자 생성 시에는 DB 고유 제약 위반을 별도로 처리해야 한다.

#### Frontend 처리

1. 사용자가 입력을 마쳤을 때 또는 중복 확인 버튼을 눌렀을 때 호출한다.
2. Query Parameter는 URL 인코딩하여 전달한다.
3. 응답의 `external_student_id`를 정규화된 최종 표시값으로 사용한다.
4. `is_available`이 `true`이면 사용 가능 상태를 표시하고 다음 단계 진행을 허용한다.
5. `is_available`이 `false`이면 중복 안내를 표시하고 사용자 생성을 차단한다.
6. 입력값이 변경되면 이전 중복 검사 결과를 무효화한다.
7. `422` 응답의 `error.details`를 해당 입력 필드에 표시한다.

#### HTTP 요청

```
GET /users/external-student-id/availability?external_student_id=DEV-001
```

#### Query Parameters

- `external_student_id`
  - 타입: string
  - 필수 여부: 필수
  - 길이: 1자 이상 100자 이하
  - 허용 조건: 공백이 아닌 문자를 최소 1개 포함
  - 정규화: 조회 전에 앞뒤 공백 제거
  - 비교 방식: 대소문자 구분 정확 일치
  - 예시: `DEV-001`

#### Request Body

- 요청 본문을 사용하지 않는다.

#### 사용 가능 응답

- 상태 코드: `200 OK`

```
{
  "external_student_id": "NEW-001",
  "is_available": true
}
```

#### 중복 응답

- 상태 코드: `200 OK`

```
{
  "external_student_id": "DEV-001",
  "is_available": false
}
```

#### 성공 응답 필드

- `external_student_id`
  - 타입: string
  - nullable: 아니요
  - 설명: 앞뒤 공백이 제거된 검사 대상 외부 학생 ID

- `is_available`
  - 타입: boolean
  - nullable: 아니요
  - 설명: 새 사용자에게 해당 ID를 사용할 수 있는지 여부

#### 입력값 검증 실패 응답

- 상태 코드: `422 Unprocessable Content`
- 오류 코드: `VALIDATION_ERROR`

```
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "요청값이 올바르지 않습니다.",
    "details": [
      {
        "field": "query.external_student_id",
        "message": "String should match pattern '^.*\\S.*$'",
        "type": "string_pattern_mismatch"
      }
    ]
  }
}
```

#### 오류 응답

- `422 Unprocessable Content`
  - 오류 코드: `VALIDATION_ERROR`
  - 발생 조건: 값 누락, 길이 초과 또는 공백만 입력
  - Frontend 처리: 외부 학생 ID 입력 필드에 검증 메시지 표시

- `500 Internal Server Error`
  - 오류 코드: `INTERNAL_SERVER_ERROR`
  - 발생 조건: 예상하지 못한 서버 또는 DB 오류
  - Frontend 처리: 잠시 후 다시 검사하도록 안내

#### 화면 갱신

조회 API이므로 사용자 데이터를 변경하지 않는다.

응답에 따라 외부 학생 ID 입력 필드의 사용 가능 상태만 갱신한다.

#### Frontend 주의사항

- 중복 검사 응답만 믿고 사용자 생성 성공을 가정하지 않는다.
- 중복 검사 후 실제 생성 전 다른 요청이 같은 ID를 생성할 수 있으므로 생성 API의 중복 오류도 처리한다.
- 입력값이 변경되면 검사 완료 표시와 제출 가능 상태를 초기화한다.
- 빠른 연속 입력에서는 이전 요청을 취소하거나 최신 응답만 반영한다.

### `GET /users/{user_id}`

#### 기능

UUID를 사용하여 사용자 상세 정보를 조회한다.

현재 개발 단계에서는 개발용 사용자의 UUID로 API를 테스트한다.

#### 연결 화면

- 사용자 프로필 화면
- 게임 상단 사용자 정보 영역
- 보유 재화 표시 영역
- 하우징 설정 화면
- 마일리지 및 사용자 진행 상태 표시

#### 인증 및 권한

- 현재 인증 필요 여부: 없음
- 현재 허용 역할: 모든 사용자
- 현재 본인 데이터 확인 여부: 구현 예정
- 권한 검사 구현 단계: 현재 사용자 식별 및 역할별 권한 검사 단계

현재는 개발용 API 확인을 위해 UUID로 직접 조회한다.

인증 기능이 구현되면 다른 사용자의 외부 학생 ID, 재화 및 상세 정보를 조회하지 못하도록 본인 여부를 검사해야 한다.

#### Backend 처리

1. Path Parameter의 `user_id`가 올바른 UUID인지 검증한다.
2. UUID를 사용하여 `users` 테이블에서 사용자를 조회한다.
3. 사용자가 존재하지 않으면 `404 USER_NOT_FOUND`를 반환한다.
4. 사용자가 존재하면 `UserResponse` 형식으로 변환한다.
5. DB에 존재하는 실제 재화 및 하우스 정보를 반환한다.
6. 존재하지 않는 `balance` 필드를 사용하지 않고 `soft_balance`와 `hard_balance`를 구분하여 반환한다.

#### Frontend 처리

1. 조회할 사용자 UUID를 Path Parameter로 전달한다.
2. 요청 중에는 사용자 정보 로딩 상태를 표시한다.
3. `200` 응답을 받으면 프로필과 재화 정보를 화면에 반영한다.
4. `wallpaper_item_id` 또는 `floor_item_id`가 `null`이면 기본 벽지와 바닥을 표시한다.
5. `404` 응답을 받으면 사용자를 찾을 수 없다는 안내를 표시한다.
6. `422` 응답을 받으면 잘못된 사용자 ID 요청으로 처리한다.
7. 재화 값은 Frontend에서 계산하지 않고 Backend 응답을 그대로 사용한다.

#### HTTP 요청

```
GET /users/{user_id}
```

#### Path Parameters

- `user_id`
  - 타입: UUID string
  - 필수 여부: 필수
  - 설명: 조회할 사용자의 내부 UUID
  - 예시: `00000000-0000-0000-0000-000000000001`

#### Query Parameters

- 없음

#### Request Body

- 요청 본문을 사용하지 않는다.

#### 성공 응답

- 상태 코드: `200 OK`

```
{
  "id": "00000000-0000-0000-0000-000000000001",
  "external_student_id": "DEV-001",
  "username": "개발용 학습자",
  "role": "USER",
  "soft_balance": 1000,
  "hard_balance": 100,
  "mileage": 0,
  "house_level": 1,
  "wallpaper_item_id": null,
  "floor_item_id": null,
  "created_at": "2026-08-30T12:00:00+09:00"
}
```

#### 성공 응답 필드

- `id`
  - 타입: UUID string
  - nullable: 아니요
  - 설명: Backend에서 사용하는 사용자 내부 식별자

- `external_student_id`
  - 타입: string
  - nullable: 아니요
  - 설명: 외부 학생 관리 시스템의 사용자 식별자

- `username`
  - 타입: string
  - nullable: 아니요
  - 설명: 사용자 이름 또는 닉네임

- `role`
  - 타입: string
  - nullable: 아니요
  - 설명: 사용자의 역할 및 권한

- `soft_balance`
  - 타입: integer
  - nullable: 아니요
  - 설명: 사용자의 일반 재화 보유량

- `hard_balance`
  - 타입: integer
  - nullable: 아니요
  - 설명: 사용자의 특수 재화 보유량

- `mileage`
  - 타입: integer
  - nullable: 아니요
  - 설명: 중복 고양이 또는 아이템 보상에 사용하는 마일리지

- `house_level`
  - 타입: integer
  - nullable: 아니요
  - 설명: 사용자 하우스의 현재 레벨

- `wallpaper_item_id`
  - 타입: integer 또는 null
  - nullable: 예
  - 설명: 현재 적용된 벽지 아이템 ID이며, 없으면 `null`

- `floor_item_id`
  - 타입: integer 또는 null
  - nullable: 예
  - 설명: 현재 적용된 바닥 아이템 ID이며, 없으면 `null`

- `created_at`
  - 타입: ISO 8601 datetime string
  - nullable: 아니요
  - 설명: 사용자 계정 생성 시각

#### 사용자 없음 응답

- 상태 코드: `404 Not Found`
- 오류 코드: `USER_NOT_FOUND`

```
{
  "error": {
    "code": "USER_NOT_FOUND",
    "message": "사용자를 찾을 수 없습니다.",
    "details": []
  }
}
```

#### 잘못된 UUID 응답

- 상태 코드: `422 Unprocessable Content`
- 오류 코드: `VALIDATION_ERROR`

```
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "요청값이 올바르지 않습니다.",
    "details": [
      {
        "field": "path.user_id",
        "message": "Input should be a valid UUID",
        "type": "uuid_parsing"
      }
    ]
  }
}
```

#### 오류 응답

- `404 Not Found`
  - 오류 코드: `USER_NOT_FOUND`
  - 발생 조건: 해당 UUID의 사용자가 존재하지 않음
  - Frontend 처리: 사용자를 찾을 수 없다는 안내 표시

- `422 Unprocessable Content`
  - 오류 코드: `VALIDATION_ERROR`
  - 발생 조건: `user_id`가 UUID 형식이 아님
  - Frontend 처리: 잘못된 사용자 ID 요청으로 처리

- `500 Internal Server Error`
  - 오류 코드: `INTERNAL_SERVER_ERROR`
  - 발생 조건: 예상하지 못한 서버 내부 오류
  - Frontend 처리: 잠시 후 다시 시도하도록 안내

#### 화면 갱신

조회 API이므로 사용자 데이터를 변경하지 않는다.

성공 응답을 받으면 다음 화면 정보를 응답값으로 갱신한다.

- 사용자 이름
- 역할
- 일반 재화
- 특수 재화
- 마일리지
- 하우스 레벨
- 벽지 및 바닥 상태

#### Frontend 주의사항

- 재화와 마일리지는 Frontend에서 임의로 변경하거나 계산하지 않는다.
- `wallpaper_item_id`와 `floor_item_id`의 `null` 상태를 처리한다.
- `external_student_id`는 다른 사용자에게 불필요하게 노출하지 않는다.
- 현재는 개발용 UUID 조회 방식이며 인증 구현 후 본인 여부를 확인해야 한다.
- 다른 사용자 화면에는 `UserSummaryResponse`만 사용하고 상세 재화 정보는 노출하지 않는다.

---

## 9. 학습 문제 API

```text
상태: 작성 예정
```

포함할 API:

- 개념 목록 조회
- 개념별 문제 목록 조회
- 문제 상세 조회
- 힌트 조회 및 사용
- 코드 제출
- 채점 결과 조회
- 학습 이력 조회
- 취약 개념 추천

---

## 10. 상점 및 인벤토리 API

```text
상태: 작성 예정
```

포함할 API:

- 상품 목록 조회
- 상품 상세 조회
- 상품 구매
- 보유 아이템 조회

---

## 11. 하우징 API

```text
상태: 작성 예정
```

포함할 API:

- 보유 가구 조회
- 가구 배치 조회
- 가구 배치 저장
- 벽지 적용
- 바닥 적용
- 다른 사용자 하우징 조회

---

## 12. 가챠 API

```text
상태: 작성 예정
```

포함할 API:

- 가챠 정보 조회
- 1회 뽑기
- 10회 뽑기
- 가챠 결과 조회

---

## 13. 배틀 API

```text
상태: 작성 예정
```

포함할 API:

- 배틀방 생성
- 배틀방 목록 조회
- 배틀방 상세 조회
- 배틀방 참가
- 준비 상태 변경
- 배틀 시작
- 문제 제출
- 배틀 상태 조회
- WebSocket 연결
- 배틀 결과 조회

---

## 14. 랭킹 및 승급전 API

```text
상태: 작성 예정
```

포함할 API:

- 랭킹 그룹 조회
- 랭킹 그룹 참가
- 그룹별 랭킹 조회
- 승급전 시작
- 승급전 문제 조회
- 승급전 문제 제출
- 승급전 상태 및 결과 조회

---

## 15. 고양이 및 AI 대화 API

```text
상태: 작성 예정
```

포함할 API:

- 보유 고양이 조회
- 고양이 대화
- 최근 기억 조회
- 기억 목록 조회
- 기억 삭제

---

## 16. 서버 상태 API

### `GET /health`

#### 기능

FastAPI 서버와 PostgreSQL 연결 상태를 확인한다.

Backend가 PostgreSQL에 `SELECT 1`을 실행하여 실제 DB 연결 가능 여부를 검사한다.

#### 연결 화면

- Frontend 최초 실행 시 Backend 연결 상태 확인
- 개발 환경의 서버 연결 점검
- 배포 환경의 서버 상태 확인
- 운영 모니터링 및 헬스 체크

게임의 일반 화면에서 반복적으로 호출할 필요는 없다.

#### 인증 및 권한

- 인증 필요 여부: 필요 없음
- 허용 역할: 모든 사용자
- 본인 데이터 확인 여부: 해당 없음

#### Backend 처리

1. 요청마다 DB 세션을 생성한다.
2. PostgreSQL에 `SELECT 1`을 실행한다.
3. DB 연결이 정상이면 `200 OK`를 반환한다.
4. DB 연결에 실패하면 `503 Service Unavailable`을 반환한다.
5. 요청 처리가 끝나면 DB 세션을 종료한다.
6. DB 비밀번호 및 내부 예외 정보는 응답에 포함하지 않는다.

#### Frontend 처리

1. 필요한 경우 앱 시작 시 `/health`를 호출한다.
2. `200` 응답이면 Backend 연결이 정상인 것으로 처리한다.
3. `503` 응답이면 서버 또는 DB 연결 오류 안내를 표시한다.
4. 서버 연결에 실패하더라도 무제한으로 반복 요청하지 않는다.
5. 재시도가 필요하면 일정 시간 후 다시 요청하거나 사용자가 재시도 버튼을 누르게 한다.

#### Path Parameters

| 이름 | 타입 | 필수 | 설명 |
|---|---|---|---|
| 없음 |  |  |  |

#### Query Parameters

| 이름 | 타입 | 필수 | 기본값 | 설명 |
|---|---|---|---|---|
| 없음 |  |  |  |  |

#### Request Body

요청 본문을 사용하지 않는다.

#### 성공 응답

- 상태 코드: `200 OK`

```
{
  "status": "ok",
  "database": "connected"
}
```

| 필드 | 타입 | nullable | 설명 |
|---|---|---|---|
| `status` | string | 아니요 | FastAPI 서버 상태이며 정상일 때 `ok` |
| `database` | string | 아니요 | PostgreSQL 연결 상태이며 정상일 때 `connected` |

#### DB 연결 실패 응답

- 상태 코드: `503 Service Unavailable`

```
{
  "error": {
    "code": "DATABASE_UNAVAILABLE",
    "message": "데이터베이스에 연결할 수 없습니다.",
    "details": []
  }
}
```

| 필드 | 타입 | nullable | 설명 |
|---|---|---|---|
| `error.code` | string | 아니요 | DB 연결 실패 시 `DATABASE_UNAVAILABLE` |
| `error.message` | string | 아니요 | 사용자에게 전달할 수 있는 오류 설명 |
| `error.details` | array | 아니요 | 세부 오류가 없으므로 빈 배열 |

#### 오류 응답

| 상태 코드 | 오류 코드 | 발생 조건 | Frontend 처리 |
|---|---|---|---|
| `503` | `DATABASE_UNAVAILABLE` | Backend가 PostgreSQL에 연결할 수 없음 | 서버 연결 오류를 안내하고 일정 시간 후 재시도 |
| `500` | `INTERNAL_SERVER_ERROR` | 예상하지 못한 서버 내부 오류 | 잠시 후 재시도하도록 안내 |

#### 화면 갱신

이 API는 사용자 게임 데이터를 변경하지 않으므로 성공 후 다른 데이터를 다시 조회할 필요가 없다.

#### Frontend 주의사항

- `/health`는 서버 상태 확인용이며 사용자 로그인 상태를 확인하는 API가 아니다.
- 사용자 정보, 재화, 출석 및 게임 데이터는 각각의 기능 API에서 조회한다.
- 짧은 간격으로 계속 호출하지 않는다.
- Backend 주소는 Frontend 환경변수로 관리한다.
- DB 접속 정보나 실제 비밀번호를 Frontend에 저장하지 않는다.

---

## 17. 변경 이력

| 날짜 | 변경 내용 | 작성자 |
|---|---|---|
| 2026-08-30 | API 명세서 기본 구조 작성 | Backend |
| 2026-08-30 | 공통 오류 응답 및 Frontend 오류 처리 규칙 추가 | Backend |
| 2026-08-30 | 실행 환경변수, CORS 정책 및 Frontend 연동 주소 추가 | Backend |
| 2026-08-30 | `/health` 서버 및 DB 상태 확인 API 명세 추가 | Backend |
| 2026-08-30 | 사용자 상세 조회 API 및 Frontend 연동 명세 추가 | Backend |
| 2026-08-30 | 외부 학생 ID 중복 검사 Backend·Frontend 공동 명세 추가 | Backend |
| 2026-08-31 | 개발용 현재 사용자 식별 및 역할별 권한 검사 명세 추가 | Backend |
| 2026-08-31 | 오늘 출석 여부 조회 및 서비스 timezone 명세 추가 | Backend |
| 2026-08-31 | 현재 사용자 출석 체크 API 및 호환 endpoint 정책 추가 | Backend |
| 2026-08-31 | 연속 출석 계산 정책 및 날짜 경계 테스트 추가 | Backend |
| 2026-08-31 | 중복 출석·중복 보상 차단 및 rollback 정책 추가 | Backend |
