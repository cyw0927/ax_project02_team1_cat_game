# 개발용 Seed 데이터·Swagger 수동 테스트 절차

이 문서는 백엔드 기능을 구현한 뒤 **매번 DB에 데이터를 손으로 만들지 않고 반복 테스트할 수 있도록 어떤 개발용 데이터가 필요한지**, 그리고 Swagger `/docs`에서 어떤 순서로 테스트할지 정리한다.

---

## 1. Seed 데이터란

개발/테스트를 위해 미리 넣어두는 예시 데이터다.

예:

```text
테스트 사용자 3명
학습 개념 4개
문제 난이도별 여러 개
상점 가구 몇 개
고양이 마스터 몇 마리
랭킹 그룹 1개
```

운영 사용자 데이터와 섞지 않는다.

---

## 2. 최소 Seed 세트

### USERS

최소 3명 정도가 편하다.

```text
user_a : 일반 기능 테스트
user_b : 배틀 상대
user_c : 잔액 부족/권한 테스트
```

재화는 테스트 목적에 따라 서로 다르게 둔다.

### CONCEPTS

예:

```text
변수
조건문
반복문
함수
```

### TASKS

최소한 다음 유형을 준비한다.

```text
정답 가능한 정상 문제
오답 비교용 문제
Runtime Error 테스트용 문제
Timeout 테스트용 문제
is_active=false 문제
```

`test_cases` 형식은 P0 의사결정이 끝난 뒤 seed에 반영한다.

### ITEMS

```text
일반 가구
벽지
바닥
고급 아이템(정책 확정 시)
```

가격은 테스트하기 편한 예시값으로 두되 실제 기획값으로 오해하지 않게 한다.

### CATS

희귀도 정책 확정 전에는 단순 예시 master data만 둔다.

```text
cat 1
cat 2
cat 3
```

---

## 3. Seed 방식

가능한 방식:

```text
A. Python seed command
B. SQL fixture
C. pytest fixture
```

MVP 개발 편의에는 Python command 또는 테스트 fixture가 이해하기 쉽다.

중요:

```text
server/ 루트에 임시 seed123.py 같은 파일을 마구 만들지 않는다.
```

정식으로 둘 경우 위치와 실행 방법을 문서화한다.

---

## 4. Seed 재실행 안전성

seed를 여러 번 실행해도 데이터가 무한 중복되지 않는 편이 좋다.

예:

```text
고정 username 존재 여부 확인
concept name 확인
item/cat master key 확인
```

개발 DB를 완전히 초기화하고 다시 seed하는 방식도 가능하다.

---

# Swagger 수동 테스트 순서

## 5. 서버 확인

```text
GET /
→ 200
→ {"message":"server running"}
```

그 다음:

```text
/docs
```

접속.

---

## 6. 학습 조회

순서:

```text
GET /concepts
GET /tasks
GET /tasks/{task_id} (추가 구현 후)
```

확인:

- 활성 task만 보이는가
- `test_cases`가 Response에 없는가
- 없는 task는 404인가

---

## 7. 코드 제출

```text
POST /attempts
```

정상 제출 후:

```text
202 Accepted
attempt_id 확인
```

그 다음:

```text
GET /attempts/{attempt_id}
```

PENDING → 최종상태 변화를 확인한다.

Docker grading 연결 전에는 PENDING에 남을 수 있으므로 구현 단계에 맞게 판정한다.

---

## 8. 출석

```text
POST /users/{user_id}/attendance/check-in
```

첫 번째:

```text
성공
```

두 번째:

```text
409
```

DB에서도 오늘 attendance가 1행인지 확인한다.

---

## 9. 상점

먼저 잔액 충분한 사용자로 정상 구매.

```text
POST /shop/buy
```

확인:

```text
balance 감소
inventory quantity 증가
```

그 다음 잔액 부족 사용자로 409 확인.

---

## 10. 배틀

추천 순서:

```text
방 생성
→ 방 목록
→ user_b 참가
→ 참가자 목록
→ Ready
→ 방장 Start
→ Finish
```

각 단계에서 room status가 맞는지 확인한다.

동시 입장 race는 Swagger보다 별도 자동/동시성 테스트가 적합하다.

---

## 11. 승급전

```text
ranking participant 준비
→ challenge 생성
→ challenge task 확인
→ saved_code 저장
→ 만료 전/후 동작 확인
```

클라이언트가 task_ids/expires_at을 보내는 현재 초안 구조는 추후 서버 주도 규칙으로 바뀔 수 있다.

---

## 12. 하우징

```text
inventory에 item 보유
→ 가구 배치
→ 이동
→ 삭제
→ wallpaper/floor 적용
```

소유하지 않은 item 배치가 거절되는지도 확인한다.

---

## 13. 가챠

API 구현 후:

```text
충분한 재화 사용자
→ 1회 실행
→ balance 감소
→ USER_CATS 반영
```

실패/rollback 테스트는 DB 오류를 강제로 만들 수 있는 자동 테스트 쪽이 더 적합하다.

---

# DB를 같이 보는 이유

Swagger에서 200이 나온다고 끝이 아니다.

예:

```text
200 응답
그런데 balance 안 줄음
```

이면 기능은 실패다.

따라서 핵심 쓰기 API는 DBeaver 등에서 Before/After row를 함께 확인한다.

---

# 테스트 기록 양식

```text
기능:
Endpoint:
Request:
예상 Status:
실제 Status:
DB Before:
DB After:
결과: PASS / FAIL
메모:
```

팀원이 같은 양식으로 기록하면 리뷰가 쉬워진다.

---

# 결론

개발용 seed와 Swagger 수동 테스트는 초보 팀에서 특히 중요하다.

```text
같은 데이터 준비
→ 같은 순서로 API 호출
→ 같은 DB 변화 확인
```

이 과정을 반복 가능하게 만들어야 기능별 검증이 빨라진다.