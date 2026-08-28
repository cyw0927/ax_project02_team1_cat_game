# 03. 실시간 배틀

이 폴더의 C-01~C-10, API, DB, 테스트 문서는 공통 [`사용자 중심 시나리오 보강 표준`](../00_common/54_user_centered_scenario_upgrade_standard.md)을 적용한다. 마지막 한 자리 동시 입장, Ready/시작 경쟁, 제출·점수 중복, 재접속과 종료 경쟁을 서버 권위 상태로 복구한다. 실시간 방식·점수식·AFK·보상은 `TBD`다.

전체 항목별 사고·방어 연결은 [`SCENARIO_RISK_MATRIX.md`](./SCENARIO_RISK_MATRIX.md)에서 검증한다.

사용자가 방을 만들거나 참가하고 Ready 후 문제를 풀며 점수를 경쟁하는 흐름을 정리한 폴더입니다.

## 문서 읽는 순서

1. `C-01_to_C-10_detailed.md` : 방 생성·입장·Ready·시작·점수·종료 시나리오
2. `API_SPEC_DRAFT.md` : REST/WebSocket 계약 초안
3. `DB_BEFORE_AFTER.md` : 방 입장·점수·종료 전후 DB 변화
4. `TEST_CASES.md` : `NOW / AFTER / POLICY` 테스트 목록

## 현재 main 구현 상태

```text
방 목록/생성                  DONE
방 참가 + FOR UPDATE          DONE
참가자/내 방 조회             DONE
Ready                         DONE — JWT ownership은 아직 없음
ROOM_TASKS CRUD               DONE
Start                         PARTIAL — host/WAITING만 검사
Finish                        PARTIAL — FINISHED 전환만 구현
배틀 제출/채점/점수            MISSING
WebSocket/재접속               MISSING
결과/보상                     MISSING/POLICY
```

## 핵심 기준

- 마지막 한 자리 동시 입장은 `ROOMS SELECT ... FOR UPDATE`로 정원 초과를 막습니다.
- `ROOM_PARTICIPANTS(room_id,user_id)`와 `ROOM_TASKS` UNIQUE를 최종 방어선으로 사용합니다.
- 점수는 프론트가 보내는 값이 아니라 서버 채점 결과로 계산합니다.
- WebSocket은 실시간 전달 수단이고 DB가 최종 상태의 기준입니다.
- DB commit 후 WebSocket broadcast 순서를 사용합니다.
- 사용자-방-문제별 중복 득점 기록 구조가 확정되기 전 scoring을 완료 처리하지 않습니다.

주요 테이블: `ROOMS`, `ROOM_PARTICIPANTS`, `ROOM_TASKS`, `TASKS`, `USERS`.

현재 핵심 선행 결정: 최소 인원, Ready 조건, 점수 규칙, 중복 득점 저장 구조, 종료/동점/보상 정책.
