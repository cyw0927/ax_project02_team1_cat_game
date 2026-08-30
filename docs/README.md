# Project Docs

`docs/`는 프로젝트 전체 공통 문서를 관리합니다.

- `architecture/`: 시스템/백엔드/Docker 구조
- `api/`: API 공통 규칙
- `db/`: ERD, 트랜잭션, 동시성/락 정책
- `product/`: 제품 흐름과 확정 비즈니스 규칙
- `operations/`: 로컬 실행/테스트/운영 메모

전체 구현 순서와 현재 재개 지점은 [`product/implementation-roadmap.md`](product/implementation-roadmap.md)에서 관리합니다.

기능별 상세 시나리오는 기존 `scenario/` 폴더에서 계속 관리합니다.

## 역할 구분

- `docs/` = 프로젝트 전체 설명서와 공통 정책
- `scenario/` = 도메인별 상세 시나리오, API 초안, 테스트 케이스

공통 정책이 변경되면 먼저 `docs/`를 갱신하고, 해당 정책에 영향을 받는 `scenario/` 문서를 함께 확인합니다.
