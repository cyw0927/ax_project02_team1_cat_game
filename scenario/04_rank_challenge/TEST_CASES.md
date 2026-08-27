# D. 랭킹·승급전 테스트 케이스

표기:

- **NOW**: 현재 코드로 테스트 가능
- **AFTER**: 구현 후 테스트
- **POLICY**: 문제 수·시간·합격·점수·보상 확정 후 기대값 고정

---

## D-T01. 랭킹 그룹 목록 — NOW

`GET /ranking-groups`

**Then** 그룹 기본 정보 반환, DB 변경 없음.

---

## D-T02. 그룹 참가자 랭킹 — NOW

`GET /ranking-groups/{group_id}/participants`

**Then**
- 없는 group은 `404`
- 참가자는 current_rank_score 내림차순

---

## D-T03. 사용자 참여 그룹 — NOW

해당 user가 참가 중인 그룹만 반환하고 다른 사용자 데이터가 섞이지 않아야 한다.

---

## D-T04. 정상 승급전 시작 — NOW/PARTIAL

현재 Request의 user_id/task_ids/expires_at을 사용한다.

**Then**
- `201`
- RANK_CHALLENGES 1개
- RANK_CHALLENGE_TASKS가 요청 순서대로 생성
- 같은 transaction commit

---

## D-T05. 과거 expires_at 거절 — NOW

현재 서버 시각보다 미래가 아니면 `400`, challenge 생성 없음.

---

## D-T06. ranking participant 아님 — NOW

해당 group 참가자가 아니면 시작 실패, challenge 생성 없음.

---

## D-T07. active challenge 중복 — NOW

같은 user/group에 아직 만료되지 않은 IN_PROGRESS challenge가 있으면 `409`.

---

## D-T08. task_ids 중복/비활성 — NOW

- 중복 task id → `400`
- 존재하지 않거나 inactive task 포함 → `404`
- challenge/task row 생성 없음

---

## D-T09. 문제 순서 고정 — NOW

생성된 RANK_CHALLENGE_TASKS의 task_order가 시작 당시 순서대로 유지되는지 확인한다.

---

## D-T10. 코드 저장 — NOW

active challenge의 포함 task에 저장하면 성공하고 saved_code가 DB에 반영된다.

---

## D-T11. 타인 challenge 저장 — NOW/AFTER JWT

현재는 payload.user_id로 ownership을 확인한다.

JWT 도입 후에는 body user_id 위조가 불가능해야 한다.

---

## D-T12. 만료 후 코드 저장 — NOW

server now가 expires_at 이상이면 `409`, saved_code 변경 없음.

현재 challenge status가 자동 TIMEOUT으로 바뀌는지는 별도 AFTER 테스트다.

---

## D-T13. 저장 코드 복원 — AFTER

재접속 후 실제 saved_code를 본인에게만 반환하고 작성 상태를 복구할 수 있어야 한다.

현재 문제 목록은 `has_saved_code`만 제공한다.

---

## D-T14. 승급전 문제 제출 — AFTER

검증:

- JWT ownership
- IN_PROGRESS
- 미만료
- challenge에 포함된 task
- test_cases 비노출
- 서버 Sandbox 채점

---

## D-T15. 정답 is_passed 반영 — AFTER

PASSED 시 해당 RankChallengeTask만 `is_passed=true`가 되고 다른 task 상태는 건드리지 않는다.

---

## D-T16. 오답 재도전 — AFTER/POLICY

오답 후 재제출 허용 여부를 확정 규칙에 맞춰 테스트한다.

---

## D-T17. TIMEOUT — AFTER

`server_now >= expires_at` 상태의 IN_PROGRESS challenge를 조회/제출한다.

**Then** 확정 방식대로 TIMEOUT 상태가 DB에 반영되고 성공/보상 처리되지 않아야 한다.

---

## D-T18. SUCCESS — AFTER/POLICY

합격 기준을 만족하면 최초 한 번만:

```text
IN_PROGRESS → SUCCESS
→ rank score 반영
→ 성공 보상
```

이 같은 transaction 경계에서 처리되는지 확인한다.

---

## D-T19. SUCCESS 중복 처리 — AFTER

완료 로직을 두 번 실행해도 점수/보상이 두 번 반영되지 않아야 한다.

---

## D-T20. FAILED — AFTER/POLICY

실패 조건과 score 감소/보상 정책 확정 후 테스트한다.

---

## D-T21. 만료 직전 동시 제출 — AFTER/POLICY

경계시각에서 여러 제출을 보내도 서버 시각과 transaction 안의 재확인 기준이 일관되어야 한다.

프론트 카운트다운만 믿지 않는다.

---

## D-T22. 서버 재시작 후 이어하기 — AFTER

DB의 status/started_at/expires_at/saved_code로 복구되는지 확인한다.

- 만료 전 → 이어하기 정책 적용
- 만료 후 → TIMEOUT

---

# D 완료 기준

승급전은 생성 API가 있다고 완료가 아니다.

```text
start
→ task order
→ autosave/restore
→ server-time grading
→ is_passed
→ SUCCESS/FAILED/TIMEOUT
→ rank score
→ 보상 1회성
```

까지 검증한다.
