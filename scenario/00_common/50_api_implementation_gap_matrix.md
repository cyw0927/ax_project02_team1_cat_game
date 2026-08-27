# API 구현 갭 매트릭스

이 문서는 **현재 main의 실제 endpoint**와 시나리오상 필요한 endpoint를 비교한다.

표기:

```text
DONE = 현재 코드에 구현
PARTIAL = endpoint는 있지만 최신 시나리오를 완성하려면 핵심 로직이 남음
MISSING = 현재 코드에 없음
POLICY = 기획/설계 확정 후 만들어야 함
```

---

## A. 학습·채점

| 기능 | 현재 상태 | 메모 |
| --- | --- | --- |
| 개념 목록 | DONE | `GET /concepts` |
| 문제 목록 | DONE | `GET /tasks`, active만 반환 |
| 문제 상세 | MISSING | `GET /tasks/{task_id}` 후보 |
| 숙련도 조회 | DONE | user_id path 사용 |
| 시도 목록 | DONE | submitted_code 비노출 |
| 시도 결과 조회 | PARTIAL | polling 가능하나 실제 채점이 아직 없음 |
| 코드 제출 접수 | PARTIAL | PENDING 생성 + 202까지만 |
| BackgroundTask 등록 | MISSING | 제출 후 grading 연결 필요 |
| Docker 채점 | PARTIAL | executor는 있으나 learning과 미연결 |
| 정답 보상 | MISSING | 보상 규칙/중복 방어 필요 |
| 숙련도 갱신 | MISSING | 공식 미정 |
| stale PENDING 복구 | MISSING | 문서만 존재 |

---

## B. 가챠·고양이

| 기능 | 상태 | 메모 |
| --- | --- | --- |
| 고양이 master 목록 | DONE | `GET /cats` |
| 내 고양이 목록 | DONE | `GET /users/{user_id}/cats` |
| 가챠 정보/확률 조회 | MISSING/POLICY | 확률 공개 범위도 결정 필요 |
| 1회 가챠 | MISSING | 비용/중복/재화 정책 필요 |
| 다회 가챠 | MISSING/POLICY | 횟수·할인·보장 미정 |
| 가챠 결과 저장 | MISSING | USER_CATS write 없음 |
| mileage 반영 | MISSING/POLICY | 중복 정책 확정 필요 |
| 고양이 대화 | MISSING | LLM 연동 필요 |
| CAT_MEMORIES 조회/저장 | MISSING | 현재 router 없음 |

---

## C. 배틀

| 기능 | 상태 | 메모 |
| --- | --- | --- |
| 방 목록 | DONE | `GET /rooms` |
| 방 생성 | DONE | host 자동 참가 여부는 미정 |
| 방 입장 | DONE | `FOR UPDATE` 적용 |
| 참가자 목록 | DONE | username 포함 |
| 내 방 목록 | DONE | 기본 정보 조회 |
| Ready | DONE | WAITING에서 변경 |
| 문제 추가 | DONE | host + WAITING |
| 문제 삭제 | DONE | host + WAITING |
| 방 문제 목록 | DONE | test_cases 비노출 |
| 게임 시작 | PARTIAL | host/WAITING만 검사, 최소인원·Ready 등 없음 |
| 게임 종료 | PARTIAL | host가 FINISHED로 변경만 함 |
| 배틀 코드 제출 | MISSING | 일반 학습과 분리/재사용 결정 필요 |
| 서버 채점 | MISSING | Sandbox 연결 필요 |
| 점수 증가 | MISSING | duplicate scoring 설계 필요 |
| 실시간 WebSocket | MISSING | 이벤트 계약 문서만 존재 |
| 재접속 snapshot | MISSING | REST 조합/전용 endpoint 결정 필요 |
| 순위/승자 결과 | MISSING | 규칙 미정 |
| 결과 보상 | MISSING | 정확히 한 번 지급 구조 필요 |

---

## D. 랭킹·승급전

| 기능 | 상태 | 메모 |
| --- | --- | --- |
| 랭킹 그룹 목록 | DONE |  |
| 그룹 참가자 랭킹 | DONE | score desc |
| 내 랭킹 그룹 | DONE |  |
| 내 승급전 이력 | DONE |  |
| 승급전 문제 조회 | DONE | saved_code 자체는 숨기고 존재 여부만 반환 |
| 승급전 시작 | PARTIAL | 현재 client가 task_ids/expires_at 지정 |
| 코드 임시 저장 | DONE | active/expiry 검사 |
| 저장 코드 실제 복원 응답 | PARTIAL | 현재 조회는 `has_saved_code`만 반환 |
| 문제 제출/채점 | MISSING |  |
| 문제 통과 처리 | MISSING | `is_passed` write 없음 |
| timeout 확정 | MISSING | 만료된 challenge status 자동 변경 없음 |
| SUCCESS/FAILED 판정 | MISSING | 합격 기준 미정 |
| rank score 변경 | MISSING |  |
| 성공 보상 | MISSING | 1회성 필요 |

---

## E. 인증

| 기능 | 상태 | 메모 |
| --- | --- | --- |
| 회원가입 | MISSING | auth 방식 미정 |
| 로그인 | MISSING |  |
| JWT 발급 | MISSING |  |
| 현재 사용자 `/me` | MISSING |  |
| refresh | MISSING/POLICY | refresh 사용 여부 미정 |
| logout | MISSING/POLICY | token 전략에 따라 달라짐 |
| role guard | MISSING | USERS.role은 있으나 dependency 없음 |
| WebSocket 인증 | MISSING | JWT 설계 후 연결 |

현재 대부분 API가 path/body `user_id`를 신뢰한다.

---

## F. 하우징

| 기능 | 상태 | 메모 |
| --- | --- | --- |
| 하우스 조회 | DONE | 다른 사용자도 조회 가능 |
| 가구 배치 | PARTIAL | 소유/수량 검사, 동시 배치 race는 남음 |
| 가구 이동/회전 | PARTIAL | dict 전체 교체, 좌표 schema 미정 |
| 가구 제거 | DONE | Inventory는 유지 |
| wallpaper 적용 | DONE | 소유/category 검사 |
| floor 적용 | DONE | 소유/category 검사 |
| 다른 집 방문 | DONE에 가까움 | GET house 자체가 user_id 기준 조회 가능 |
| 고양이 하우징 배치 | MISSING/POLICY | 저장 구조 없음 |
| 고양이 상호작용 | MISSING | cats/LLM 쪽과 연결 필요 |

---

## G. 상점

| 기능 | 상태 | 메모 |
| --- | --- | --- |
| 아이템 목록 | DONE | 전체 item 반환 |
| category filter | MISSING | 필요 시 query filter |
| 내 inventory | DONE |  |
| 1개 구매 | DONE | Atomic UPDATE + upsert |
| 다수 구매 | MISSING/POLICY | 실제 요구 확인 |
| 판매중지 처리 | MISSING/POLICY | ITEMS is_active 없음 |
| 환불 | MISSING/POLICY | MVP 제외 가능 |
| JWT 사용자 식별 | MISSING | auth 후 변경 |

---

## H. 출석

| 기능 | 상태 | 메모 |
| --- | --- | --- |
| 수동 check-in | DONE | 현재 코드 |
| 100원 지급 | DONE | 현재 코드에 100 |
| 복합 UNIQUE 중복 방어 | DONE | model constraint |
| streak 계산 | DONE | 이전 날짜 기준 |
| 출석 기록 조회 | DONE |  |
| 첫 로그인 자동 처리 | MISSING | 확정 요구사항 |
| timezone 명시 처리 | MISSING/POLICY | 현재 `date.today()` |
| 같은 날 재로그인 무해 처리 | MISSING | auth/login 통합 후 필요 |

---

# 구현 우선순위 관점

## 이미 테스트 중심으로 다듬으면 되는 것

```text
상점 구매
출석 transaction 자체
하우징 기본 CRUD
배틀 lobby
승급전 생성/코드저장
```

## 연결 작업이 가장 중요한 것

```text
POST /attempts
→ BackgroundTask
→ Sandbox
→ 최종상태
→ 보상
```

## 설계 결정을 먼저 해야 하는 것

```text
가챠 중복/재화
배틀 scoring 중복 방어
배틀 결과 보상 1회성
승급전 합격/점수/보상
인증/JWT
고양이 하우징 배치
```

---

# 사용 원칙

기능 하나를 구현할 때 이 표의 상태를:

```text
MISSING
→ PARTIAL
→ DONE
```

으로 갱신한다.

`DONE`은 endpoint가 존재한다는 뜻만이 아니라 관련 시나리오의 핵심 검증/transaction/권한까지 충족했는지 확인한 뒤 붙인다.
