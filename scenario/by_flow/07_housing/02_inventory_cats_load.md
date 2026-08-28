# 02. 보유 가구 및 고양이 로드

## 목적
사용자가 하우징에서 실제로 사용할 수 있는 가구와 고양이를 서버 보유 상태 기준으로 확정한다.

## 정상 흐름
1. INVENTORIES에서 보유 item과 quantity를 조회한다.
2. PLACED_OBJECTS와 비교해 현재 배치 수량을 계산한다.
3. USER_CATS와 CATS를 조회해 보유 고양이 목록을 구성한다.
4. 인벤토리/고양이 선택 UI를 렌더링한다.

## 발생 가능한 변수
### A. inventory quantity보다 이미 배치된 수량이 많음
- 원인: 과거 버그, 동시 배치 race, 마이그레이션 오류.
- 해결: 클라이언트에서 조용히 삭제하지 않는다. 서버 권위 상태로 표시하고 복구 정책을 별도로 둔다.

### B. 구매 직후 새 아이템이 안 보임
- 원인: 이전 화면 캐시, 오래된 API 응답.
- 해결: 하우징 진입 시 inventory를 재조회한다.

### C. starter 고양이가 없음
- 원인: 가입/로그인 starter 보장 로직이 아직 실행되지 않음.
- 해결: 기존 starter 보장 서비스 로직을 재사용한다. 프론트가 임의 DB row를 만들지 않는다.

### D. USER_CATS 중복
- 원인: 동시 starter 생성/가챠 중복 처리 race.
- 해결: 중복 허용 여부가 정책상 불가능하면 `(user_id, cat_id)` DB 제약 도입 여부를 확정한다. 현재 스키마에 확정되지 않은 제약은 문서에서 구현 완료로 가정하지 않는다.

### E. 아이템 category가 예상과 다름
- 원인: 잘못된 master 데이터.
- 해결: 가구/벽지/바닥 UI에서 category를 서버 master 기준으로 검증한다.

## UI
- 보유 수량, 현재 배치 수량을 구분한다.
- 배치 불가능하면 이유를 표시한다.
- asset 누락 고양이는 fallback을 사용하되 소유권을 잃은 것처럼 보이지 않게 한다.

## 다음 단계 조건
가구 선택 → `03_furniture_place_edit.md`
벽지/바닥 선택 → `04_wallpaper_floor.md`
고양이 상호작용 → `05_cat_display_interaction.md`

## 테스트
- inventory 0개
- 구매 직후 진입
- quantity < placed count 비정상 데이터
- starter 없음
- USER_CATS 중복
- item category 오류
