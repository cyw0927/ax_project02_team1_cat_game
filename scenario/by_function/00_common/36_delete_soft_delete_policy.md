# 삭제·소프트삭제 정책

이 문서는 데이터를 실제로 DELETE할지, 비활성화 상태로 남길지 기능별 기준을 정리한다.

## 1. 기본 원칙

사용 이력과 다른 테이블이 참조하는 마스터 데이터는 함부로 물리 삭제하지 않는다.

```text
물리 삭제
= row 자체 제거

소프트 삭제/비활성화
= row는 유지하고 더 이상 신규 사용만 막음
```

## 2. TASKS

현재 `is_active`가 이미 있다.

문제 오류나 운영 중지 시:

```text
DELETE보다 is_active=false 권장
```

이유:

- 기존 TASK_ATTEMPTS가 task를 참조
- 과거 학습 이력 보존
- 다시 활성화 가능

일반 사용자 목록/상세에서는 비활성 task를 숨긴다.

## 3. ITEMS

이미 INVENTORIES, PLACED_OBJECTS가 참조할 수 있다.

판매 중단이 필요하면 장기적으로 `is_active`/`is_for_sale` 같은 상태 추가를 검토한다.

현재 스키마에 해당 컬럼이 없다면 실제 기능 도입 시 migration 여부를 결정한다.

이미 사용자가 가진 가구를 마스터에서 지워 하우스 렌더링이 깨지는 상황을 피한다.

## 4. CATS

USER_CATS가 참조하는 고양이 마스터도 물리 삭제에 주의한다.

신규 가챠 후보에서 제외하고 싶다면 활성 여부 컬럼 같은 정책을 나중에 검토할 수 있다.

## 5. CONCEPTS

TASKS/USER_PROFICIENCY가 연결될 수 있으므로 이미 사용된 concept는 단순 DELETE보다 비활성 정책을 고려한다.

## 6. TASK_ATTEMPTS

학습 이력/채점 감사 기록 성격이므로 일반 사용자 기능에서 DELETE하지 않는 것을 기본으로 한다.

재제출은 기존 attempt 삭제/덮어쓰기가 아니라 새 row 추가다.

## 7. RANK_CHALLENGES

승급전 결과 이력도 보존한다.

```text
SUCCESS
FAILED
TIMEOUT
```

같은 완료 기록을 삭제하면 사용자 진행 내역과 디버깅 근거가 사라진다.

## 8. ROOMS

방은 목적에 따라 다르다.

MVP 후보:

```text
WAITING 방 취소
→ 실제 삭제 가능 여부 검토

FINISHED 방
→ 기록이 필요하면 유지
```

배틀 기록/보상 추적을 사용할 예정이면 FINISHED 방을 즉시 지우지 않는 편이 안전하다.

## 9. ROOM_PARTICIPANTS

WAITING 상태 퇴장은 실제 DELETE가 자연스러울 수 있다.

하지만 IN_PROGRESS/FINISHED의 참가 기록은 점수·결과와 연결되므로 삭제하지 않는 정책을 우선 검토한다.

정확한 중도 이탈 정책이 확정되면 다시 정한다.

## 10. PLACED_OBJECTS

가구를 방에서 치우는 것은 실제 DELETE가 자연스럽다.

중요:

```text
PLACED_OBJECTS DELETE
≠
INVENTORIES quantity 감소
```

사용자는 가구 소유권을 그대로 유지한다.

## 11. INVENTORIES

보유 수량이 0이 되는 소비형 아이템이 생긴다면:

```text
A. quantity=0 row 유지
B. row DELETE
```

둘 중 하나를 팀에서 통일한다.

현재 가구 구매 중심이면 0 수량 상황 자체가 거의 없을 수 있다.

## 12. USERS

사용자 탈퇴가 MVP 범위에 없다면 물리 삭제 API를 서둘러 만들 필요 없다.

향후 탈퇴가 들어오면 개인정보 삭제와 게임 기록 보존 요구가 충돌할 수 있으므로 별도 설계가 필요하다.

## 13. FK와 삭제

DB FK에 무조건 `ON DELETE CASCADE`를 걸지 않는다.

예:

```text
TASK 삭제
→ 과거 TASK_ATTEMPTS까지 전부 삭제
```

가 자동으로 일어나면 위험하다.

어떤 자식 row를 정말 같이 없애야 하는지 테이블별로 판단한다.

## 14. API 응답

실제 DELETE 성공 시 보통:

```http
204 No Content
```

또는 프로젝트 계약에 맞춘 200 Response를 사용할 수 있다.

이미 없는 자원을 다시 삭제할 때 404로 할지 idempotent success로 할지는 endpoint 성격에 맞춰 통일한다.

## 핵심

삭제는 화면에서 안 보이게 하는 것과 DB에서 기록을 없애는 것이 다르다.

특히 **학습/랭킹/배틀 이력과 다른 테이블이 참조하는 마스터 데이터는 보존 우선**, 하우징 배치처럼 현재 상태만 표현하는 데이터는 실제 삭제를 사용할 수 있다.