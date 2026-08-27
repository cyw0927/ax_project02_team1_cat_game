# G. 상점 테스트 케이스

표기:

- **NOW**: 현재 코드로 테스트 가능
- **AFTER**: 보완 구현 후 테스트
- **POLICY**: 재화 종류·다수 구매·판매중지·환불 규칙 확정 후 기대값 고정

---

## G-T01. 아이템 목록 — NOW

`GET /items`

**Then**
- `200`
- id/category/name/price 반환
- DB 변경 없음

---

## G-T02. Inventory 조회 — NOW

`GET /users/{user_id}/inventory`

**Then**
- 해당 user 보유 item만 반환
- quantity 포함
- 없는 user는 `404`

---

## G-T03. 정상 1개 구매 — NOW

충분한 balance를 가진 사용자로 `POST /shop/buy`.

**Then**
- 서버 ITEMS.price 기준으로 차감
- INVENTORIES quantity 증가
- 최종 current_balance 반환
- 동일 transaction에서 commit

---

## G-T04. 프론트 가격 위조 방지 — NOW

현재 Request에는 가격 필드가 없다.

**Then** item_id만으로 서버 가격을 사용해야 한다.

---

## G-T05. 잔액 부족 — NOW

**Then**
- `409`
- balance 변화 없음
- Inventory 변화 없음

---

## G-T06. 존재하지 않는 item — NOW

`404`, balance/Inventory 변화 없음.

---

## G-T07. 동일 item 재구매 — NOW

처음 구매 후 다시 구매한다.

**Then** 새 Inventory row를 중복 생성하지 않고 기존 `(user_id,item_id)` row의 quantity가 1 증가한다.

---

## G-T08. 동시 구매 잔액 방어 — NOW

잔액이 1개 가격만큼만 남은 사용자에게 동시에 여러 구매 요청을 보낸다.

**Then**
- 허용 가능한 요청만 성공
- balance 음수 없음
- 성공 횟수와 Inventory 증가량 일치

Atomic conditional UPDATE를 검증한다.

---

## G-T09. Inventory 저장 실패 rollback — NOW 테스트 작성 필요

balance 차감 이후 Inventory upsert에서 강제로 DB 오류를 발생시킨다.

**Then** transaction rollback으로 balance도 원복되어야 한다.

---

## G-T10. 응답 최종값 동기화 — NOW

구매 Response의 `current_balance`, `quantity`가 실제 DB commit 후 값과 일치해야 한다.

---

## G-T11. 버튼 연타 — NOW/POLICY

현재는 성공한 각 요청을 별도 정상 구매로 처리한다.

네트워크 재전송을 한 번만 인정하기로 한다면 AFTER에 idempotency key 테스트를 추가한다.

---

## G-T12. category filter — AFTER

화면 요구가 확정되어 filter API를 추가하면 허용 category와 결과 0건을 정상 처리하는지 확인한다.

---

## G-T13. 다수 구매 — AFTER/POLICY

quantity 구매를 지원한다면:

- quantity validation
- `server price × quantity`
- Atomic 총액 차감
- Inventory quantity 증가
- 중간 실패 rollback

을 검증한다.

---

## G-T14. 판매중지 — AFTER/POLICY

ITEMS.is_active 등 구조를 도입할 경우:

- 기존 Inventory는 유지
- 신규 구매만 거절
- 목록 노출 정책 일치

을 확인한다.

---

## G-T15. JWT ownership — AFTER

사용자 A가 B의 user_id를 보내도 B의 balance/Inventory를 수정할 수 없어야 한다.

최종 구매 사용자는 JWT 기준.

---

## G-T16. 다중 재화 — AFTER/POLICY

재화 구조가 실제로 변경될 때만:

- item이 어떤 재화를 사용하는지
- 해당 재화만 차감
- 다른 재화는 변화 없음
- Response 필드 일치

를 추가 테스트한다.

---

## G-T17. 환불 — AFTER/POLICY

MVP에 포함할 경우 배치 중 아이템/수량/반환 재화 정책까지 함께 검증한다.

현재는 구현하지 않은 기능으로 유지한다.

---

# G 완료 기준

상점 핵심은:

```text
서버 가격
→ Atomic 차감
→ Inventory upsert
→ 같은 transaction
→ 실패 rollback
→ 최종값 Response
```

이 흐름이 동시 요청에서도 깨지지 않는 것이다.
