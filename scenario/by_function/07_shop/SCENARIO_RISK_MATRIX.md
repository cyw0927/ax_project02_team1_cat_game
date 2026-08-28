# G-01~G-10 사용자 사고 시나리오 추적표

| 항목·화면/정상 흐름 | 대표 Worst Case·원인 | 서버 감지·방어 | UI·DB/state·다음 단계·테스트/TBD |
|---|---|---|---|
| G-01 진입 | 목록/잔액 일부 실패 | 조회별 성공·활성 item 검증 | 빈 상점으로 위장 금지 |
| G-02 필터 | 조작된 category/대량 조회 | allowlist·pagination/상한 | 안전한 빈 결과/오류 |
| G-03 확인 모달 | 열린 뒤 가격 변경 | 구매 시 DB 가격 재조회 | 가격 변경 알림; 클라이언트 가격 불신 |
| G-04 구매 | 차감 성공 후 inventory 실패 | 조건부 원자 UPDATE+INVENTORIES 증가를 한 짧은 transaction | 성공 시 최신 잔액/수량 |
| G-05 부족 | 오래된 화면은 충분 표시 | 차감 영향 row=0 | 변경 없이 부족 안내 |
| G-06 매크로 | 버튼 연타/응답 지연으로 다중 구매 | request idempotency 정책 `TBD`, 조건부 차감 | 처리 중 잠금은 보조; 연속 구매와 재시도 구분 |
| G-07 재구매 | inventory row 생성 경쟁 | `(user,item)` unique+UPSERT 후보 | 최신 quantity 표시; 단일성 정책 `TBD` |
| G-08 없는 상품 | 오래된 탭/item_id 위조 | 존재·활성·판매 가능 검증 후 차감 | 결제 없음, 목록 재조회 |
| G-09 rollback | inventory 예외 뒤 돈만 빠짐 | 같은 transaction 전체 rollback | 실패 애니메이션, 잔액 재조회 |
| G-10 완료 | commit 후 응답 유실·앱 크래시 | 거래 결과 조회/idempotency `TBD` | `구매 여부 확인 중`; 임의 재구매 금지; 하우징 재조회 |

Docker/외부 호출/사용자 확인 중 transaction이나 lock을 유지하지 않는다.

