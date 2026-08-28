# 05. 로그인·회원가입·인증

이 폴더의 E-01~E-10, API, DB, 테스트 문서는 공통 [`사용자 중심 시나리오 보강 표준`](../00_common/54_user_centered_scenario_upgrade_standard.md)을 적용한다. 가입 연타, 계정 존재 추측, 토큰 만료 중 write, user_id 위조와 여러 기기 로그아웃을 UI·권한·후속 상태까지 연결한다.

전체 항목별 사고·방어 연결은 [`SCENARIO_RISK_MATRIX.md`](./SCENARIO_RISK_MATRIX.md)에서 검증한다.

사용자가 계정을 만들고 로그인한 뒤 JWT 등 인증 정보를 이용해 본인 권한으로 API를 호출하는 흐름을 정리한 폴더입니다.

## 문서 읽는 순서

1. `E-01_to_E-10_detailed.md` : 회원가입·로그인·JWT·권한 시나리오
2. `API_SPEC_DRAFT.md` : 인증 API 계약 초안
3. `DB_BEFORE_AFTER.md` : 가입·로그인·자동 출석 연결 전후 DB 변화
4. `TEST_CASES.md` : `NOW / AFTER / POLICY` 테스트 목록

## 현재 main 구현 상태

```text
USERS 기본 모델               DONE
회원가입/로그인               MISSING
password_hash / username UNIQUE POLICY/MISSING
JWT 발급·검증                MISSING
/me                          MISSING
role guard                   MISSING
자동 출석 로그인 연결         MISSING
WebSocket 인증               MISSING
```

## 핵심 기준

- 비밀번호 원문은 DB/로그/Response 어디에도 저장·노출하지 않습니다.
- 보호 API의 사용자 식별은 최종적으로 body/path `user_id`가 아니라 인증된 현재 사용자를 기준으로 합니다.
- 인증 실패는 `401`, 인증은 됐지만 권한이 없으면 `403`으로 구분합니다.
- 로그인 성공 후 자동 출석 서비스를 호출하되 출석 내부에서는 `ATTENDANCES INSERT + 100원 지급`을 같은 transaction으로 처리합니다.
- 같은 날 재로그인 시 이미 출석했다는 이유로 로그인 자체가 실패하면 안 됩니다.

주요 테이블: `USERS`, 로그인 자동 출석 연결 시 `ATTENDANCES`.

현재 핵심 선행 결정: 로컬 로그인/소셜 로그인, username UNIQUE, password_hash/email 필요 여부, access/refresh token 정책, role 범위, 서비스 timezone.
