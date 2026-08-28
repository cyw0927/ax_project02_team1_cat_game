# A-01~A-10 사용자 사고 시나리오 추적표

공통 표준의 모든 필드를 A 영역 각 항목에 적용한다. DB/API 상세는 기존 문서를 보존한다.

| 항목·화면/정상 흐름 | 대표 Worst Case·원인 | 서버 감지·방어 | UI·DB/state·다음 단계·테스트/TBD |
|---|---|---|---|
| A-01 문제 상세 진입 | 오래된 목록에서 비활성 문제 선택 | 존재·활성 상태 재검증, test_cases 비노출 | 목록 복귀; DB write 없음; 비활성 경쟁 테스트 |
| A-02 제출 | 버튼 매크로·응답 지연으로 중복 제출 | 입력 schema/크기, attempt/request 식별; 각 제출과 중복 영향 분리 | `제출 중/결과 확인 중`; PENDING만 짧게 저장; commit 후 유실 테스트 |
| A-03 PENDING | 대량 제출로 컨테이너 폭증 | 대기/실행 수·오래된 PENDING 감지; 단일-worker MVP는 semaphore | 대기 표시; BackgroundTasks는 durable queue 아님; 재시작/stuck 테스트 |
| A-04 PASSED | 같은 정답 결과 콜백 2회로 보상 중복 | attempt 최종 상태·보상 키 확인; 조건부 상태 전이+멱등 지급 | 최초 정답/기지급 표시; 보상·재화로 안전하게 handoff |
| A-05 WRONG_ANSWER | 테스트 데이터 오류를 사용자 오답으로 기록 | 실행 성공 여부와 테스트 판정 분리 | 오답과 시스템 오류 분리; 재제출 정책 `TBD` |
| A-06 RUNTIME_ERROR | 사용자 코드가 컨테이너 밖 자원 접근 | exit/result 분류; network none/read-only/최소 권한 | 실행 오류만 표시; 호스트/DB 영향 없음; 탈출 시도 테스트 |
| A-07 TIMEOUT | 무한루프·출력 폭주·메모리 고갈 | wall timeout, CPU/memory/output 상한 | 시간 초과 표시; system 상태 정상 유지; 자원별 테스트 |
| A-08 SYSTEM_ERROR | Docker daemon/worker 재시작으로 작업 유실 | 오래된 PENDING·worker 오류 로그 | 오답 처리 금지; 복구/재시도 정책 `TBD`; durable queue 전환 조건 기록 |
| A-09 재제출 | 이전 느린 결과가 최신 화면을 덮음 | attempt_id별 결과, 응답 순서 검증 | 최신 선택 attempt만 강조; 과거 기록 보존; 역순 완료 테스트 |
| A-10 보상 | 정답 commit 뒤 네트워크 단절로 재지급 요청 | reward event unique/ledger `TBD`; 기존 결과 반환 | 지급 애니메이션 반복 금지; 최신 balance 재조회; 보상 수치 `TBD` |

