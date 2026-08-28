# 08. 출석

이 폴더의 H-01~H-10, API, DB, 테스트 문서는 공통 [`사용자 중심 시나리오 보강 표준`](../00_common/54_user_centered_scenario_upgrade_standard.md)을 적용한다. 23:59→00:01 경계, 두 기기 첫 로그인, 기록 성공 뒤 보상 실패와 응답 유실을 서버 날짜·unique·짧은 transaction으로 검증한다. 일일 미션 완료용 가상 컬럼을 출석 테이블에 만들지 않는다.

전체 항목별 사고·방어 연결은 [`SCENARIO_RISK_MATRIX.md`](./SCENARIO_RISK_MATRIX.md)에서 검증한다.

**매일 자정 이후 첫 로그인 시 자동 출석 1회 + 100원 지급** 흐름을 정리한 폴더입니다.

## 문서 읽는 순서

1. `H-01_to_H-10_detailed.md` : 자동 출석·streak·중복·자정 경계 시나리오
2. `API_SPEC_DRAFT.md` : 현재 수동 check-in과 최종 자동 출석 API/서비스 차이
3. `DB_BEFORE_AFTER.md` : 출석·100원 지급·rollback 전후 DB 변화
4. `TEST_CASES.md` : `NOW / AFTER / POLICY` 테스트 목록

## 현재 main 구현 상태

```text
수동 check-in endpoint           DONE
ATTENDANCES 하루 UNIQUE          DONE
streak 계산                      DONE
100원 지급                       DONE
출석 + 보상 transaction          DONE
출석 기록 조회                   DONE
첫 로그인 자동 출석 연결          MISSING
같은 날 재로그인 no-op           MISSING
명시적 service timezone         POLICY/MISSING
JWT 사용자 식별                  MISSING
```

## 확정 기준

```text
매일 자정 이후 첫 로그인
→ 서버 기준 오늘 날짜 판정
→ 오늘 첫 출석이면 ATTENDANCES INSERT
→ 100원 지급
→ 같은 transaction COMMIT
```

- `(user_id, check_in_date)` UNIQUE가 하루 1회 처리의 최종 방어선입니다.
- 같은 날 다시 로그인하는 것은 정상 행동이므로 이미 출석했다는 이유로 로그인 자체가 실패하면 안 됩니다.
- 출석 기록은 생겼는데 보상만 실패하는 상태가 없도록 출석과 보상을 같은 transaction으로 처리합니다.
- 클라이언트가 보내는 날짜나 PC 시간을 믿지 않습니다.
- 현재 코드의 `date.today()`는 서버 OS timezone에 의존하므로 최종 서비스 timezone 확정 뒤 명시적으로 계산해야 합니다.

주요 테이블: `USERS`, `ATTENDANCES`.

현재 남은 핵심 결정은 **서비스 기준 timezone**, 로그인 Response에 출석 결과를 포함할지, 수동 check-in endpoint를 최종 사용자 API로 남길지입니다.
