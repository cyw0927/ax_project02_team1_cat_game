# F-01~F-10 사용자 사고 시나리오 추적표

| 항목·화면/정상 흐름 | 대표 Worst Case·원인 | 서버 감지·방어 | UI·DB/state·다음 단계·테스트/TBD |
|---|---|---|---|
| F-01 내 방 진입 | 조회 실패를 빈 방으로 저장 | 조회 성공/소유자 검증 | 실패와 빈 방 구분; write 없음 |
| F-02 인벤토리 | 구매 직후 오래된 캐시 | 서버 inventory/placed 재조회 | 최신 보유량 표시 |
| F-03 배치 | quantity=1을 두 탭에서 각각 배치 | 소유·배치 수량을 짧은 원자 처리 | 하나만 확정; 배치 규칙 `TBD` |
| F-04 미소유 배치 | item_id 위조 | 인증 user의 INVENTORIES 확인 | 403/검증 오류; PLACED_OBJECTS 불변 |
| F-05 수량 초과 | 동시 요청/과거 데이터 오류 | 보유량·배치량·unique/constraint 후보 | 복구 안내; 정책 `TBD` |
| F-06 이동 | 타인 object id 또는 두 기기 덮어쓰기 | owner·version 확인 후보 | 403/충돌 복원; 병합 정책 `TBD` |
| F-07 회전 | 비정상 각도/배치 데이터 폭탄 | schema·허용값·payload 상한 | 부분 저장 금지; rotation 규칙 `TBD` |
| F-08 치우기 | 삭제 연타·commit 후 응답 유실 | owner/기존 상태 확인, 이미 없음은 복구 가능 응답 | inventory 소유량은 감소하지 않음 |
| F-09 벽/바닥 | furniture category 위조 | 소유권+category 동시 검증 | 서버 확정 surface 표시 |
| F-10 공개 방문 | 타인 수정·쓰다듬기 매크로·보상 유실 | 방문자 read-only, 403, 방문 event 멱등/일일 제한 | 동일 결과 복원; 신규 ERD 필요, 횟수·보상 `TBD` |

AI 대화는 특정 공급자를 전제하지 않는다. 입력 검증·역할/권한 분리·출력 검증·최소 권한·방문자 read-only·CAT_MEMORIES 쓰기 제한·로깅/모니터링을 적용한다.

