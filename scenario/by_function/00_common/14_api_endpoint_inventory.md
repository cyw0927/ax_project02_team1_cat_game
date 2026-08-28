# 전체 API 엔드포인트 목록 초안

이 문서는 현재 시나리오를 실제 개발 가능한 API 단위로 쪼개기 위한 임시 목록이다. 아직 URL은 확정 계약이 아니며, 기존 구현과 통합하면서 정리한다.

## A. 학습·채점

| 기능 | Method | Endpoint 예시 | 핵심 테이블 |
|---|---|---|---|
| 개념 목록 | GET | `/concepts` | CONCEPTS |
| 문제 목록 | GET | `/tasks` | TASKS |
| 문제 상세 | GET | `/tasks/{task_id}` | TASKS, CONCEPTS |
| 숙련도 조회 | GET | `/users/{user_id}/proficiency` | USER_PROFICIENCY |
| 문제 제출 | POST | `/attempts` | TASK_ATTEMPTS |
| 채점 결과 조회 | GET | `/attempts/{attempt_id}` | TASK_ATTEMPTS |
| 사용자 풀이 이력 | GET | `/users/{user_id}/attempts` | TASK_ATTEMPTS |

## B. 가챠

| 기능 | Method | Endpoint 예시 | 핵심 테이블 |
|---|---|---|---|
| 가챠 정보 조회 | GET | `/gacha` | USERS, CATS |
| 단일/다회 뽑기 | POST | `/gacha/pulls` | USERS, CATS, USER_CATS |
| 내 고양이 조회 | GET | `/users/{user_id}/cats` | USER_CATS, CATS |

## C. 배틀

| 기능 | Method | Endpoint 예시 | 핵심 테이블 |
|---|---|---|---|
| 방 목록 | GET | `/rooms` | ROOMS |
| 방 생성 | POST | `/rooms` | ROOMS, ROOM_PARTICIPANTS |
| 방 입장 | POST | `/rooms/{room_id}/join` | ROOMS, ROOM_PARTICIPANTS |
| 준비 변경 | PATCH | `/rooms/{room_id}/ready` | ROOM_PARTICIPANTS |
| 게임 시작 | POST | `/rooms/{room_id}/start` | ROOMS, ROOM_TASKS |
| 방 문제 조회 | GET | `/rooms/{room_id}/tasks` | ROOM_TASKS, TASKS |
| 배틀 제출 | POST | `/rooms/{room_id}/attempts` | ROOM_PARTICIPANTS, TASKS |
| 배틀 종료 | POST | `/rooms/{room_id}/finish` | ROOMS, ROOM_PARTICIPANTS, USERS |
| 실시간 연결 | WS | `/ws/rooms/{room_id}` | 방 상태/점수 이벤트 |

## D. 승급전

| 기능 | Method | Endpoint 예시 | 핵심 테이블 |
|---|---|---|---|
| 랭킹 조회 | GET | `/ranking-groups/{group_id}` | RANKING_PARTICIPANTS |
| 승급전 시작 | POST | `/ranking-groups/{group_id}/rank-challenges` | RANK_CHALLENGES, RANK_CHALLENGE_TASKS |
| 진행 중 승급전 조회 | GET | `/users/{user_id}/rank-challenge` | RANK_CHALLENGES |
| 승급전 문제 조회 | GET | `/rank-challenges/{challenge_id}/tasks` | RANK_CHALLENGE_TASKS, TASKS |
| 코드 저장 | PUT | `/rank-challenges/{challenge_id}/tasks/{task_id}/code` | RANK_CHALLENGE_TASKS |
| 문제 제출 | POST | `/rank-challenges/{challenge_id}/tasks/{task_id}/submit` | RANK_CHALLENGE_TASKS |
| 승급전 결과 | GET | `/rank-challenges/{challenge_id}` | RANK_CHALLENGES |

## E. 인증

| 기능 | Method | Endpoint 예시 | 비고 |
|---|---|---|---|
| 회원가입 | POST | `/auth/signup` | USERS 구조 확장 필요 |
| 로그인 | POST | `/auth/login` | JWT 발급 |
| 토큰 재발급 | POST | `/auth/refresh` | Refresh 사용 여부 미정 |
| 내 정보 | GET | `/auth/me` | JWT에서 user 식별 |

## F. 하우징

| 기능 | Method | Endpoint 예시 | 핵심 테이블 |
|---|---|---|---|
| 내/다른 집 조회 | GET | `/users/{user_id}/house` | USERS, PLACED_OBJECTS, ITEMS |
| 가구 배치 | POST | `/users/{user_id}/house/objects` | INVENTORIES, PLACED_OBJECTS |
| 가구 이동/회전 | PATCH | `/users/{user_id}/house/objects/{object_id}` | PLACED_OBJECTS |
| 가구 치우기 | DELETE | `/users/{user_id}/house/objects/{object_id}` | PLACED_OBJECTS |
| 벽지 적용 | PUT | `/users/{user_id}/house/wallpaper` | USERS, INVENTORIES |
| 바닥 적용 | PUT | `/users/{user_id}/house/floor` | USERS, INVENTORIES |

## G. 상점

| 기능 | Method | Endpoint 예시 | 핵심 테이블 |
|---|---|---|---|
| 상품 목록 | GET | `/shop/items` | ITEMS |
| 상품 구매 | POST | `/shop/buy` | USERS, ITEMS, INVENTORIES |
| 인벤토리 조회 | GET | `/users/{user_id}/inventory` | INVENTORIES, ITEMS |

## H. 출석

| 기능 | Method | Endpoint 예시 | 핵심 테이블 |
|---|---|---|---|
| 오늘 출석 | POST | `/users/{user_id}/attendance/check-in` | ATTENDANCES, USERS |
| 출석 기록 | GET | `/users/{user_id}/attendances` | ATTENDANCES |

## 공통 확인

- 인증 완료 후 user_id를 body에서 직접 받는 API는 가능한 한 JWT 기반으로 전환한다.
- 모든 endpoint를 `/api/v1`로 묶을지는 팀에서 별도 결정한다.
- 실제 기존 코드와 충돌하는 URL은 구현 시 한 번에 통일한다.
- 이 목록은 Swagger 기준표와 프론트-백엔드 계약표의 초안으로 사용한다.
