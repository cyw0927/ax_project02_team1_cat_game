# API 버전·호환성 정책

이 문서는 프론트와 백엔드가 동시에 개발되는 동안 API 형태가 바뀌어도 서로 작업이 갑자기 깨지지 않도록 최소 기준을 정리한다.

## 1. MVP 기본 원칙

현재 프로젝트 규모에서는 처음부터 `/api/v1/...` 같은 복잡한 버전 체계를 반드시 도입할 필요는 없다. 다만 한 번 프론트가 사용하는 Request/Response 계약을 잡았다면 사소한 이유로 필드명과 의미를 계속 바꾸지 않는다.

예:

```text
좋지 않은 변경
balance → coin → money → feed

좋은 변경
재화 기획이 확정될 때 한 번 명확히 변경
→ 관련 API/ERD/문서를 같이 수정
```

## 2. 호환되는 변경

대체로 다음은 기존 프론트를 덜 깨뜨린다.

- Response에 선택 필드 추가
- 새로운 endpoint 추가
- 기존 optional query parameter 추가
- 기존 의미를 유지한 내부 구현 변경

예:

```json
기존
{"id": 1, "name": "캣타워"}

추가 후
{"id": 1, "name": "캣타워", "category": "furniture"}
```

기존 프론트가 추가 필드를 무시할 수 있다면 비교적 안전하다.

## 3. 호환되지 않는 변경

- endpoint URL 변경
- HTTP Method 변경
- 필수 Request 필드 추가
- Response 필드 삭제/이름 변경
- status code 의미 변경
- 같은 필드의 자료형 변경

예:

```text
price: int
→
price: string
```

이런 변경은 프론트 수정과 같이 진행한다.

## 4. user_id 제거 시점

현재 인증 전 API 일부는 body/path에서 `user_id`를 받는다.

JWT 도입 후에는:

```text
클라이언트가 user_id 전달
→ 서버가 JWT의 사용자 ID 사용
```

으로 바뀌는 것이 바람직하다.

이것은 호환성 영향이 큰 변경이므로 한 API씩 제각각 바꾸기보다 인증 도입 시점에 관련 API 목록을 정해 일괄 수정한다.

## 5. 재화 구조 변경

현재 `USERS.balance`, `mileage`가 있지만 기획에서 사료/금화/마일리지 등 여러 재화가 확정될 수 있다.

이 경우 DB 컬럼만 바꾸고 끝내지 않는다.

함께 확인:

```text
상점 Response
가챠 Response
출석 Response
학습 보상 Response
배틀/승급전 보상 Response
프론트 HUD
seed/test 데이터
```

## 6. Deprecated 처리

MVP 단계에서는 오래된 API를 장기간 유지할 필요는 없지만, 프론트가 이미 붙은 API를 바로 삭제하지 않는다.

팀 내에서:

```text
1. 새 API/필드 제공
2. 프론트 전환 확인
3. 기존 API 제거
```

순서를 지킨다.

## 7. 변경 기록

큰 API 계약 변경은 PR 설명이나 scenario 문서에 남긴다.

예:

```text
변경 전: POST /shop/buy {user_id, item_id}
변경 후: POST /shop/buy {item_id}
이유: JWT에서 user_id 추출
프론트 영향: body에서 user_id 제거
```

## 8. 버전 경로를 도입해야 하는 시점

다음 상황이면 `/api/v1` 검토 가치가 있다.

- 외부 사용자/앱이 이미 기존 API를 사용
- 모바일 앱처럼 구버전 클라이언트를 즉시 업데이트할 수 없음
- 운영 중 큰 구조 개편이 필요

현재 팀 프로젝트 MVP에서는 문서화된 단일 계약을 유지하는 것이 우선이다.

## 핵심

API 버전 정책의 목적은 숫자 `v1`을 붙이는 것이 아니라 **프론트와 백엔드의 약속을 예측 가능하게 바꾸는 것**이다.