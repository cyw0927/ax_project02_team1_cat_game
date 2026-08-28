# 입력 Validation 정책

이 문서는 프론트가 보내는 값을 백엔드가 어디까지 검증해야 하는지 공통 기준을 정리한다.

## 1. 기본 원칙

프론트에서 이미 검사했더라도 서버는 다시 검증한다.

```text
프론트 validation = 사용자 편의
백엔드 validation = 데이터 보호
```

직접 API를 호출하면 프론트 검사를 우회할 수 있기 때문이다.

## 2. 형식 검증

FastAPI/Pydantic에서 먼저 막을 수 있는 것:

- UUID 형식
- int/string/bool 자료형
- 필수 필드 누락
- 문자열 최소/최대 길이
- 숫자 최소/최대값
- list 최소/최대 개수

잘못된 형식은 일반적으로 `422 Unprocessable Entity`로 처리할 수 있다.

## 3. 존재 여부 검증

형식이 맞아도 DB에 실제 대상이 있는지 확인한다.

예:

```text
task_id는 UUID 형식 정상
하지만 TASKS에 없음
→ 404
```

대상:

- user
- task
- item
- room
- participant
- ranking group
- challenge
- placed object
- cat

## 4. 상태 검증

존재해도 현재 상태에서 행동 가능한지 본다.

예:

```text
비활성 task 제출
FINISHED room 참가
만료된 rank challenge 코드 저장
```

이런 경우 단순 형식 오류가 아니라 비즈니스 상태 충돌이므로 `409 Conflict` 등을 검토한다.

## 5. 권한·소유권 검증

ID를 안다고 수정할 수 있는 것이 아니다.

예:

```text
다른 사용자의 가구 이동
다른 방의 participant ready 변경
비방장의 room start
다른 사용자의 challenge saved_code 변경
```

JWT 적용 후 요청자 identity는 토큰에서 가져온다.

## 6. 문자열 입력

### submitted_code

사용자 코드이므로 일반 텍스트보다 길 수 있다. 정확한 최대 크기는 서버 설정으로 둘 수 있다.

검토:

```text
빈 문자열 허용 여부
최대 길이
NUL 등 비정상 문자
```

코드 내용의 안전성은 문자열 금칙어 필터만으로 해결하지 않고 Sandbox가 최종 방어한다.

### username

인증 방식 확정 후:

```text
최소/최대 길이
허용 문자
공백 처리
대소문자 중복 정책
UNIQUE
```

을 정한다.

## 7. 숫자 입력

클라이언트가 가격/보상/점수를 결정하도록 하지 않는다.

나쁜 예:

```json
{"item_id": 5, "price": 1}
```

좋은 예:

```json
{"item_id": 5}
```

서버가 ITEMS.price를 조회한다.

배틀 점수도 프론트가 `score=9999`를 보내서 올리는 구조를 피한다.

## 8. Enum 형태 값

상태나 category는 허용 목록을 둔다.

예:

```text
ROOM status: WAITING, IN_PROGRESS, FINISHED
challenge status: IN_PROGRESS, SUCCESS, FAILED, TIMEOUT
```

임의 문자열을 저장하지 않는다.

## 9. JSONB position_data

현재 하우징 위치가 JSONB라서 너무 자유로운 입력이 들어올 수 있다.

최종 스키마가 확정되면 최소한:

```json
{"x": 2, "y": 4, "rotation": 90}
```

같이 필요한 key와 자료형, 허용 범위를 Pydantic schema로 검증하는 것이 좋다.

## 10. list 입력

승급전 `task_ids` 같은 리스트는:

- 빈 리스트 금지
- 중복 ID 금지
- 최대 개수
- 모든 task 존재/활성 확인

이 필요하다.

## 11. 서버가 계산해야 할 값

다음은 가능하면 client 입력에서 제거한다.

```text
현재 시각
출석 날짜
상품 가격
보상량
현재 사용자 ID(JWT 이후)
승급전 expires_at(서버 고정 규칙 도입 시)
배틀 점수
```

## 12. 테스트

각 쓰기 API에서 최소:

- 정상 입력
- 필수값 누락
- 잘못된 자료형
- 없는 FK 대상
- 허용 범위 초과
- 권한 없음
- 현재 상태에서 불가능한 요청

을 확인한다.

## 핵심

Validation은 단순히 Pydantic이 422를 내는 것만이 아니다.

```text
형식
→ 존재
→ 상태
→ 권한
→ 비즈니스 규칙
```

순서로 서버가 데이터를 믿을 수 있는지 확인해야 한다.