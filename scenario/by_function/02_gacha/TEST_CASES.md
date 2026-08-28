# B. 가챠·고양이 테스트 케이스

표기:

- **NOW**: 현재 코드로 테스트 가능
- **AFTER**: 구현 후 테스트
- **POLICY**: 가격·확률·중복·천장 등 기획 확정 후 기대값 고정

---

## B-T01. 고양이 마스터 목록 — NOW

`GET /cats`

**Then**
- `200`
- id/name/persona/rarity 반환
- DB 변경 없음

---

## B-T02. 사용자 보유 고양이 — NOW

`GET /users/{user_id}/cats`

**Then**
- 해당 user의 USER_CATS만 반환
- CATS master 정보와 정상 join
- 없는 user는 `404`

---

## B-T03. 정상 1회 가챠 — AFTER/POLICY

유효한 사용자와 충분한 재화를 준비한다.

**Then**
- 서버가 비용을 결정
- 재화 차감
- 서버가 결과 추첨
- USER_CATS 또는 확정 중복 보상 반영
- 하나의 transaction으로 commit
- 최종 잔액과 결과를 Response로 반환

---

## B-T04. 프론트 결과 위조 방지 — AFTER

Request에 임의의 cat_id/rarity/가격을 넣으려 해도 서버가 받지 않거나 무시해야 한다.

당첨 결과와 비용은 서버 기준이어야 한다.

---

## B-T05. 잔액 부족 — AFTER

**Then**
- `409` 등 확정 상태코드
- 재화 변화 없음
- USER_CATS 변화 없음
- mileage/티켓 변화 없음

---

## B-T06. 결과 저장 실패 rollback — AFTER

재화 차감 직후 USER_CATS 저장에서 DB 오류를 강제로 발생시킨다.

**Then** 전체 rollback되어 사용자가 돈만 잃지 않아야 한다.

---

## B-T07. 중복 요청/버튼 연타 — AFTER/POLICY

동일한 요청이 네트워크 재전송으로 두 번 도착한 상황과 사용자가 실제로 두 번 뽑은 상황을 구분하는 정책을 테스트한다.

idempotency를 채택한다면 동일 key는 한 번만 실행돼야 한다.

---

## B-T08. 동시 가챠 잔액 방어 — AFTER

잔액이 1회분만 남은 사용자에게 동시에 여러 pull 요청을 보낸다.

**Then** 허용된 횟수만 성공하고 잔액이 음수가 되면 안 된다.

재화 차감은 Atomic UPDATE 등 확정된 동시성 방어를 사용한다.

---

## B-T09. 확률 분기 단위 테스트 — AFTER/POLICY

랜덤 함수를 테스트 가능한 방식으로 주입/고정하여 각 확률 구간이 올바른 결과 그룹으로 매핑되는지 검증한다.

실제 확률 숫자는 기획 확정값을 사용한다.

---

## B-T10. 다회 가챠 — AFTER/POLICY

다회를 지원하는 경우:

- 허용 pull_count 검증
- 총 비용 서버 계산
- 결과 개수 일치
- 보장 규칙이 있다면 적용
- 중간 하나 저장 실패 시 transaction 정책 확인

---

## B-T11. 중복 고양이 — AFTER/POLICY

정책별 기대값을 확정한 뒤 테스트한다.

예:

```text
중복 별도 소유
또는
mileage/티켓 전환
```

현재 DB에는 `(user_id, cat_id)` UNIQUE가 없으므로 정책 확정 전에 테스트가 구조를 강제하지 않는다.

---

## B-T12. mileage 반영 — AFTER/POLICY

중복 보상이 mileage라면:

- 정확한 delta
- 최종 mileage
- 가챠 transaction과 함께 commit
- rollback 시 mileage도 원복

을 확인한다.

---

## B-T13. 천장 — AFTER/POLICY

천장을 도입할 경우:

- 누적 횟수 증가
- 발동 조건
- 발동 후 reset 조건
- 단일/다회 카운트
- 서버 재시작 후 누적 유지

를 검증한다.

현재 전용 저장 구조가 없으므로 스키마 결정 선행.

---

## B-T14. JWT ownership — AFTER

로그인한 사용자 A가 user B의 UUID를 보내도 B의 재화/USER_CATS가 변경되면 안 된다.

최종 쓰기 기준은 JWT 사용자다.

---

## B-T15. 고양이 대화 ownership — AFTER

다른 사용자의 `user_cat_id`로 대화를 요청하면 거절한다.

---

## B-T16. LLM 실패 — AFTER

외부 LLM timeout/error 발생 시:

- 고양이 소유 데이터는 영향 없음
- 열린 DB transaction을 오래 유지하지 않음
- 사용자에게 처리 가능한 오류 반환

---

## B-T17. CAT_MEMORIES 갱신 — AFTER/POLICY

memory 구조 확정 후:

- 올바른 USER_CAT memory만 읽기/쓰기
- 다른 사용자 memory 변경 불가
- summary 갱신 실패가 USER_CATS 소유권을 손상시키지 않음

---

# B 완료 기준

가챠 핵심은 연출보다 데이터 안전성이다.

```text
서버 비용/결과 결정
→ 재화 차감
→ 결과 지급
→ 하나의 transaction
→ 중복/동시요청 방어
```

이 흐름이 먼저 통과해야 한다.
