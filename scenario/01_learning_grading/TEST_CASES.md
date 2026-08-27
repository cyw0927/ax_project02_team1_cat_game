# A. 학습·채점 테스트 케이스

이 문서는 `API_SPEC_DRAFT.md`의 내용을 실제 테스트 항목으로 옮긴다.

표기:

- **NOW**: 현재 코드로 바로 테스트 가능
- **AFTER**: 해당 기능 구현 후 테스트
- **POLICY**: 기획 확정 뒤 기대값을 고정

---

## A-T01. 개념 목록 조회 — NOW

**Given** CONCEPTS 데이터가 존재한다.

**When** `GET /concepts`

**Then**
- `200`
- id/name 반환
- DB 변경 없음

---

## A-T02. 활성 문제 목록 조회 — NOW

**When** `GET /tasks`

**Then**
- `is_active=true` 문제만 반환
- `test_cases`는 Response에 없음
- `template_code`, difficulty 등 화면용 필드 반환

---

## A-T03. 비활성 문제 비노출 — NOW

활성/비활성 TASK를 함께 준비한 뒤 `/tasks`를 호출한다.

**Then** inactive task id가 결과에 없어야 한다.

---

## A-T04. 정상 제출 접수 — NOW

**When** 유효한 user/task/code로 `POST /attempts`

**Then**
- `202 Accepted`
- TASK_ATTEMPTS 1개 생성
- `status=PENDING`
- submitted_code는 DB에 저장
- Response는 채점 완료를 의미하지 않음

---

## A-T05. 없는 사용자 제출 — NOW

**Then** `404`, TASK_ATTEMPTS 생성 없음.

---

## A-T06. 없는/비활성 문제 제출 — NOW

**Then** `404`, TASK_ATTEMPTS 생성 없음.

---

## A-T07. 결과 polling — NOW/PARTIAL

`GET /attempts/{attempt_id}` 호출 시 현재 attempt 상태를 반환한다.

현재 grading 미연결 상태에서는 PENDING이 유지될 수 있다.

**AFTER** 구현 후에는 PENDING/RUNNING에서 최종 상태로 전환되는지 확인한다.

---

## A-T08. 사용자 제출 이력 — NOW

**Then**
- 해당 user의 attempt만 반환
- 최신순
- submitted_code 전체는 목록 Response에 노출하지 않음

---

## A-T09. BackgroundTask 즉시 반환 — AFTER

동시에 Docker가 오래 걸리는 코드를 제출해도 HTTP 요청은 채점 완료까지 기다리지 않고 `202`를 반환해야 한다.

---

## A-T10. Docker 자원 제한 — AFTER

확정 요구사항을 실제 컨테이너에서 검증한다.

- memory 128MB
- CPU 0.5
- network none
- read-only filesystem
- container cleanup

---

## A-T11. Docker 동시 실행 제한 — AFTER

여러 제출을 동시에 보낸다.

**Then**
- PENDING은 여러 개 생길 수 있음
- 실제 실행 컨테이너 수는 설정된 제한을 넘지 않음

multi-worker에서는 process-local semaphore 한계를 별도 확인한다.

---

## A-T12. 정상 정답 — AFTER

**Then**
- 최종 status가 확정 규칙의 PASSED 계열
- `is_correct=true`가 필요하다면 일치
- 보상/숙련도는 확정 규칙에 따라 반영

---

## A-T13. 오답 — AFTER

**Then**
- WRONG_ANSWER 계열 상태
- HTTP 자체는 서버 오류가 아님
- 정답 보상 없음

---

## A-T14. Runtime Error — AFTER

예: NameError/SyntaxError 등 사용자 코드 오류.

**Then** 사용자 오류 상태로 저장되고 서버 `500` 장애와 구분된다.

---

## A-T15. Timeout — AFTER

무한 루프 코드를 제출한다.

**Then**
- 설정된 제한 이후 종료
- TIMEOUT 상태
- container 제거
- 보상 없음

정확한 timeout 숫자는 POLICY.

---

## A-T16. Docker/System Error — AFTER

Docker Engine 연결 실패나 이미지 없음 등을 강제로 만든다.

**Then** SYSTEM_ERROR 계열로 기록되고 PENDING/RUNNING에 영구 고착되지 않아야 한다.

---

## A-T17. stale PENDING 복구 — AFTER

BackgroundTask가 유실된 PENDING을 준비한다.

**Then** stale 정책 이후 SYSTEM_ERROR 등 확정 상태로 정리되고 사용자는 재제출 가능해야 한다.

---

## A-T18. 재제출 — AFTER

같은 문제에 여러 번 제출하면 시도 이력을 각각 남긴다.

무제한 재시도 여부는 POLICY지만, 현재 구조에서는 attempt row를 새로 만드는 방식을 기준으로 본다.

---

## A-T19. 중복 정답 보상 — AFTER/POLICY

같은 사용자·같은 문제의 정답 attempt를 거의 동시에 완료시킨다.

**Then** 확정된 보상 횟수보다 더 많이 지급되지 않아야 한다.

단순 `이전 PASSED 없음 SELECT`만으로 끝내지 않는다.

---

## A-T20. test_cases 보안 — NOW/AFTER

문제 목록, 상세, attempt 결과 등 일반 사용자 Response 어디에서도 hidden test_cases가 노출되지 않는지 확인한다.

---

# A 완료 기준

학습은 단순히 `POST /attempts`가 202를 반환한다고 완료가 아니다.

```text
조회
→ 제출
→ PENDING
→ 제한된 Docker 실행
→ 최종 상태
→ polling 종료
→ 보상 중복 방어
```

까지 통과해야 핵심 루프가 완료된다.
