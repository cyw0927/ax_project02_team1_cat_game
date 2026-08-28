# API Overview

이 문서는 프로젝트의 API 공통 역할을 빠르게 파악하기 위한 인덱스입니다. 상세 요청/응답과 실패 시나리오는 `scenario/`의 각 도메인 문서를 기준으로 합니다.

## 현재 주요 API 영역

- Users / Attendance
- Learning / Attempts
- Battle / Rooms
- Ranking / Rank Challenges
- Economy / Shop / Inventory
- Housing
- Cats / User Cats / Starter Cat

## 공통 원칙

- 사용자 식별은 최종적으로 JWT 기반으로 이동할 예정이며, 현재 일부 API는 임시로 body/path의 `user_id`를 사용합니다.
- 장시간 작업은 요청 transaction 안에서 수행하지 않습니다.
- 리소스 없음은 404, 상태 충돌은 409를 기본으로 사용합니다.
- 아직 구현되지 않은 API를 프론트에서 실제 연동된 것처럼 가정하지 않습니다.

상세 API 초안은 `scenario/*/API_SPEC_DRAFT.md`를 참고합니다.
