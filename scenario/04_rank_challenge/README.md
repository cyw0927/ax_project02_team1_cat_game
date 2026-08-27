# 04. 랭킹·승급전

사용자가 소규모 랭킹을 확인하고 승급전에 도전해 문제를 풀고 성공/실패 판정을 받는 흐름을 정리한 폴더입니다.

## 문서 읽는 순서

1. `D-01_to_D-10_detailed.md` : 승급전 사용자 시나리오
2. `API_SPEC_DRAFT.md` : 랭킹/승급전 API 계약 초안
3. `DB_BEFORE_AFTER.md` : challenge 생성·저장·완료 전후 DB 변화
4. `TEST_CASES.md` : `NOW / AFTER / POLICY` 테스트 목록

## 현재 main 구현 상태

```text
랭킹 그룹/참가자 조회            DONE
사용자 랭킹 그룹/도전 이력        DONE
승급전 시작                       PARTIAL
승급전 문제 목록                  DONE
코드 임시 저장                    DONE
saved_code 실제 복원              PARTIAL
문제 제출/채점                    MISSING
is_passed / TIMEOUT               MISSING
SUCCESS / FAILED                  MISSING/POLICY
rank score / 성공 보상            MISSING/POLICY
```

## 핵심 기준

- challenge와 challenge task들은 시작 시 같은 transaction에서 생성합니다.
- 제한시간은 프론트 카운트다운이 아니라 서버 시각과 `expires_at`으로 판정합니다.
- 재접속 시 DB의 `saved_code`, `is_passed`, `expires_at`을 기준으로 복구합니다.
- `IN_PROGRESS → SUCCESS` 최초 상태 전환을 점수/보상 1회성의 기준으로 사용합니다.
- 현재 클라이언트가 `task_ids`와 `expires_at`을 보내지만, 문제 수/시간이 서버 규칙으로 확정되면 Request를 단순화하는 방향을 검토합니다.

주요 테이블: `RANKING_GROUPS`, `RANKING_PARTICIPANTS`, `RANK_CHALLENGES`, `RANK_CHALLENGE_TASKS`, `TASKS`.

현재 핵심 선행 결정: 문제 수, 제한시간, 문제 선정 주체, 합격/실패 기준, 점수 증감, 성공 보상, 재도전 정책.
