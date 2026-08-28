# E-01~E-10 사용자 사고 시나리오 추적표

| 항목·화면/정상 흐름 | 대표 Worst Case·원인 | 서버 감지·방어 | UI·DB/state·다음 단계·테스트/TBD |
|---|---|---|---|
| E-01 가입 화면 | 클라이언트 규칙만 믿고 악성 입력 | 서버 schema/길이/허용값 검증 | 필드 오류, DB write 없음 |
| E-02 가입 | 버튼 연타로 사용자/초기자산 중복 | username unique, 가입 초기화 transaction/멱등 후보 | 기존 결과/로그인 유도; starter 중복 테스트 |
| E-03 중복 이름 | 동시 가입이 사전 SELECT 통과 | DB unique가 최종 방어 | 계정 존재를 과도하게 노출하지 않는 오류 |
| E-04 잘못된 입력 | 과대 payload·스크립트 문자열 | 크기·정규화·schema 검증 | 안전한 필드 오류 |
| E-05 로그인 | 성공 직후 출석/초기화 일부 실패 | 인증과 부가 write 경계·rollback 정책 | 로그인/출석 결과 구분 |
| E-06 비밀번호 오류 | 계정 존재 추측·brute force | 동일한 외부 오류, rate limit/로그 | 민감 원인 미노출 |
| E-07 토큰 만료 | write commit 뒤 401 응답처럼 인식 | 인증 시점·거래 결과 id 확인 | 재로그인 뒤 결과 조회; refresh 정책 `TBD` |
| E-08 user_id 위조 | 타인의 id로 자산 API 호출 | token subject와 resource owner 비교 | 403/404 계약; 타인 state 불변 |
| E-09 로그아웃 | 다른 기기 세션까지 의도치 않게 종료 | token/session 범위 확인 | 현재/전체 기기 선택 정책 `TBD` |
| E-10 role | 일반 사용자가 admin API 호출 | 서버 role allowlist | 403; 감사 로그; UI 숨김은 보조 |

