# 공용 저장소와 개인 저장소 구조 비교

비교 기준은 2026-08-28에 각 원격 저장소의 최신 기본 브랜치(`main`)를 fetch한 결과다.

- 공용: `KANT-2/cat-game`, `1a6066e`
- 개인: `cyw0927/ax_project02_team1_cat_game`, 작업 시작점 `8b66dd4`

공용 저장소는 비교용으로만 읽었으며 push URL을 비활성화했다.

## 요약

공용 저장소는 **Vite + TypeScript + PixiJS 기반 단일 PWA 프론트엔드**이며, 현재 서버나 DB 구현은 없다. 개인 저장소는 **정적 HTML/JavaScript 프로토타입과 FastAPI/PostgreSQL 백엔드를 분리**하고 Alembic, API 테스트, 상세 시나리오 문서를 포함한다. 두 저장소는 같은 제품을 다루지만 현재 앱 계층과 도구 체인이 달라 파일 단위 병합보다 계약을 정한 뒤 기능을 이식하는 방식이 안전하다.

## 항목별 비교

| 기준 | 공용 저장소 | 개인 저장소 | 병합 시 판단 |
| --- | --- | --- | --- |
| top-level | `src`, `public`, `tests`, `scripts`, `docs`와 Vite 설정 | `prototype`, `server`, `docs`, `scenario` | 동일 경로 충돌은 적지만 앱 진입점이 둘이 될 위험이 큼 |
| frontend/prototype | `src/app`, `assets`, `content`, `core`, `domain`, `game`, `pwa`, `services`; PixiJS Canvas | `prototype/game.html`, `css`, `js`, `assets`; DOM 기반 플레이어블 목업 | 개인 프로토타입을 그대로 공용 `src`에 복사하지 말고 화면/동작 요구를 PixiJS scene과 `GameClient`로 이식 |
| backend/server | 없음. `GameClient`와 `LocalGameClient`가 향후 원격 구현 경계를 제공 | `server/app` 아래 users/learning/battle/ranking/economy/housing/cats 도메인별 FastAPI 구조 | 서버는 개인 구조가 기준. 프론트는 원격 `GameClient` 어댑터로 API를 호출하는 방향 권장 |
| docs/scenario | PDR, PLAN, ARCHITECTURE, CODE_GUIDE, TEAM_WORKFLOW, ADR 33개 | 공통 `docs`와 도메인별 상세 `scenario` | 문서 역할 중복 가능. 공용 ADR/PDR을 결정 기록의 기준으로 두고 개인 scenario는 API·DB 상세 근거로 연결 |
| 실행 방식 | `npm install`, `npm run dev`(5173), build/check/test/smoke/PWA smoke | FastAPI(8000) + 정적 서버(5500) 두 프로세스 | 통합 시 프론트는 Vite, 서버는 FastAPI로 유지하고 개발 프록시 또는 명시적 API base 설정 필요 |
| env/config | `vite.config.ts`, PWA manifest; 런타임 env 없음 | `server/.env.example`, `DATABASE_URL`, sandbox 설정 | `VITE_API_BASE_URL` 같은 프론트 환경 변수와 CORS 허용 origin을 팀 합의로 추가할 후보 |
| DB/migration | 없음, localStorage 저장소만 존재 | SQLAlchemy, PostgreSQL, Alembic initial migration | DB 스키마와 권위 상태는 개인 서버를 기준으로 검토. LocalGameClient 데이터와 서버 DTO 매핑 필요 |
| 테스트 | Vitest 단위 테스트, 구조/asset 검사, Playwright smoke, PWA smoke | pytest API 계약 및 sandbox 테스트; 프론트 자동 테스트 없음 | 양쪽 테스트를 모두 유지. API 계약 테스트와 프론트 원격 클라이언트/가챠 DEMO smoke를 추가하는 것이 좋음 |

## 충돌 가능성이 큰 지점

1. `index.html`과 앱 시작 방식: 공용은 Vite의 루트 진입점, 개인은 `prototype/index.html` 리다이렉트다.
2. 게임 상태의 소유권: 공용 `LocalGameClient`는 로컬 상태를 권위 있게 다루지만 개인 서버는 사용자·재화·고양이·하우징 DB를 권위 상태로 둔다.
3. UI 기술: PixiJS Canvas와 DOM/CSS 화면을 한 화면에서 섞으면 입력, 크기 조정, z-index, 접근성 처리 방식이 충돌한다.
4. 자산 경로: 공용은 `public/assets/catalog.json`의 안정 ID를 요구하고 개인은 상대 파일 경로를 JavaScript에 직접 매핑한다.
5. 문구 관리: 공용은 `src/content/ko.json`, 개인은 HTML/JavaScript 문자열이다.
6. 좌표/충돌: 공용은 논리 격자와 isometric 변환, 개인은 화면 percentage 좌표와 사각 장애물이다.
7. 실행 포트/CORS: 공용 Vite 기본 5173은 현재 개인 서버의 허용 origin 목록에 없다.

## 개인 저장소에서 미리 맞춰두면 좋은 항목

- API 요청/응답을 DOM 코드에서 분리한 `api.js` 경계는 유지하고, 장차 공용 `GameClient`를 구현하는 원격 어댑터의 계약 초안으로 사용한다.
- 고양이/가구 자산에 파일 경로 외 안정적인 catalog ID를 부여한다. `cat.orange.walk`, `cat.black.walk`, `cat.white.walk`처럼 이름을 먼저 합의한다.
- 사용자 노출 문구를 기능 키로 분리해 이후 `src/content/ko.json`으로 옮기기 쉽게 한다.
- percentage 이동 좌표와 서버 `position_data`, 공용 격자 좌표 사이 변환 책임을 별도 모듈로 둔다.
- 백엔드 CORS에 5173을 추가하기 전 팀 실행 방식과 env 정책을 먼저 확정한다.
- 공용 명명에 맞춰 프론트 개념은 `app/core/domain/game/services` 책임으로 문서화하되, 현재 플레이 가능한 `prototype` 폴더를 성급히 이동하지 않는다.
- 가챠 가격·확률·당첨 결과는 FastAPI 서버가 결정하며 프론트는 결과 표시와 재조회만 담당한다.

## 권장 통합 순서

1. FastAPI OpenAPI 계약과 공용 `GameClient` 사이의 원격 어댑터 인터페이스를 합의한다.
2. 사용자/보유 고양이/하우징 조회처럼 이미 구현된 read 흐름부터 연결한다.
3. 실제 가챠·배틀 API와 선택 고양이 클릭 이동 UI 방향을 공용 PixiJS scene 요구사항으로 이식한다.
4. 공용 asset catalog와 content catalog에 개인 자산·문구를 등록한다.
5. Vite smoke + FastAPI contract test를 함께 실행하는 통합 검증을 만든다.
