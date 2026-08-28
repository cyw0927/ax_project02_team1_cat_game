# 04. 벽지·바닥 적용

## 목적
일반 가구 배치와 다른 방식으로 적용되는 wallpaper/floor 아이템을 사용자 보유 상태에 맞춰 변경한다.

## 정상 흐름
1. 사용자가 보유 목록에서 벽지 또는 바닥 아이템을 선택한다.
2. 서버가 item 존재 여부와 category를 확인한다.
3. INVENTORIES에서 사용자 보유 여부를 확인한다.
4. wallpaper면 USERS.wallpaper_item_id, floor면 USERS.floor_item_id를 갱신한다.
5. 성공 응답 후 클라이언트가 방 배경을 갱신한다.

## 발생 가능한 변수
### A. 가구 item을 wallpaper/floor로 위조해 요청
- 원인: 클라이언트 조작.
- 해결: 서버에서 category를 다시 검증한다.

### B. 보유하지 않은 벽지/바닥 적용
- 해결: 화면 표시와 무관하게 서버가 INVENTORIES를 확인해 거절한다.

### C. 현재 적용된 item master가 삭제/비활성화
- 원인: 운영 데이터 변경.
- 해결: 사용자의 저장 상태를 임의 초기화하지 않는다. fallback 표시 후 운영 복구 정책에 따라 처리한다.

### D. 두 기기에서 서로 다른 벽지를 동시에 적용
- 결과: 마지막 성공 update가 최종 상태가 된다.
- 필요 시 version 기반 충돌 감지 검토.

### E. 적용 성공 후 응답 유실
- 해결: 재접속 또는 재조회에서 USERS의 최신 적용값을 읽는다. 화면이 실패했다고 임의 복원하지 않는다.

## DB/API 영향
- USERS.wallpaper_item_id
- USERS.floor_item_id
- INVENTORIES 소유권 검증
- ITEMS.category 검증

## UI
- 선택 중 preview와 서버 저장 완료 상태를 구분한다.
- 저장 실패 시 이전 확정 상태로 되돌리거나 미저장 표시.

## 테스트
- 정상 wallpaper/floor 적용
- 잘못된 category
- 비보유 item
- item master 누락
- 두 기기 동시 변경
- commit 후 응답 유실
