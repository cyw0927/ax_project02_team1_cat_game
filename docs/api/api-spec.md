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

현재 사용자 식별 방식은 사용자 기능 구현 단계에서 확정한다.

```text
상태: 미확정
후보: Authorization 헤더 또는 개발용 사용자 헤더
```

인증 방식이 확정되면 다음 내용을 기록한다.

- 필요한 요청 헤더
- 로그인 또는 사용자 식별 과정
- 인증 실패 응답
- 역할별 접근 권한
- 토큰 만료 및 재인증 방법

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

- `GET /users/{user_id}` 사용자 상세 조회
- `GET /users/external-student-id/availability` 외부 학생 ID 중복 검사

작성 예정 API:

- 사용자 생성
- 오늘 출석 여부 조회
- 출석 체크
- 일일 미션 완료 처리

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
