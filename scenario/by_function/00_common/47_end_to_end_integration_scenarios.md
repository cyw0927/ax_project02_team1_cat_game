# E2E 통합 시나리오

이 문서는 각 기능을 따로 테스트한 뒤 **실제 사용자 흐름처럼 여러 도메인을 이어서 검증하는 방법**을 정리한다.

단위 기능이 모두 정상이어도 연결 과정에서 문제가 생길 수 있다.

예:

```text
학습 채점은 성공
상점 구매도 성공

하지만 학습 보상으로 늘어난 balance가
상점 Response에 반영되지 않음
```

이런 문제는 도메인별 테스트만으로 놓칠 수 있다.

---

# E2E-01. 로그인 → 자동 출석 → 홈

## 목적
확정된 출석 요구사항을 실제 로그인 흐름으로 검증한다.

## 흐름

```text
오늘 처음 로그인
→ 인증 성공
→ 서버 기준 오늘 날짜 계산
→ ATTENDANCES 생성
→ 100원 지급
→ 홈 진입
```

## 확인

```text
ATTENDANCES 오늘 row = 1
USERS balance = 이전값 + 100
로그인/홈 응답에서 필요한 출석 정보 전달
```

## 같은 날 두 번째 로그인

```text
로그인 성공
→ 오늘 attendance 이미 존재
→ 추가 보상 없음
→ 홈 정상 진입
```

중복 출석 때문에 로그인 자체가 실패하면 안 된다.

---

# E2E-02. 학습 → 제출 → Docker 채점 → 보상

## 흐름

```text
학습 화면
→ 문제 선택
→ 코드 작성
→ POST /attempts
→ 202 + PENDING
→ BackgroundTask
→ Docker 채점
→ PASSED
→ 보상 자격 확인
→ USERS 재화 증가
→ polling 최종 결과 표시
```

## 확인

- `test_cases`는 프론트에 노출되지 않음
- 제출 직후 HTTP 요청이 Docker 완료까지 기다리지 않음
- PENDING/RUNNING/최종상태 흐름 정상
- 최초 보상 규칙에 맞게 재화 지급
- 같은 문제 반복 정답 시 중복 보상 규칙 준수
- Docker container cleanup

보상 숫자/일일 제한은 기획 확정값을 사용한다.

---

# E2E-03. 학습 보상 → 상점 → 하우징

최신 제품 흐름의 핵심 소비 루프다.

```text
학습으로 재화 획득
→ 상점 열기
→ 가구 구매
→ Inventory 증가
→ 하우징 열기
→ 구매한 가구 배치
```

## DB 흐름

```text
USERS 재화 증가
→ 상점 구매에서 재화 감소
→ INVENTORIES quantity 증가
→ PLACED_OBJECTS 생성
```

## 확인

- 상점 가격은 서버 `ITEMS.price` 기준
- 잔액 부족 시 Inventory 증가 없음
- 구매 성공 시 최종 잔액 Response 일치
- Inventory에 없는 가구는 배치 불가
- 배치 후 Inventory quantity 자체는 감소하지 않음
- 보유 quantity보다 더 많이 배치할 수 없는지 확인

---

# E2E-04. 재화 → 가챠 → 고양이 보유

## 흐름

```text
사용자 재화 보유
→ 가챠 실행
→ 서버 비용 확인
→ Atomic 차감
→ 고양이 결과 결정
→ USER_CATS 반영
→ 결과 화면
```

## 확인

- 비용/확률은 서버 기준
- 차감과 결과 저장이 같은 transaction
- 저장 실패 시 재화 원복
- 중복 고양이 정책 적용
- mileage 정책이 있다면 같은 transaction에서 처리
- 같은 네트워크 요청 재전송 시 중복 실행 정책 확인

정확한 가격/확률/천장은 기획 확정 전 임의로 넣지 않는다.

---

# E2E-05. 고양이 획득 → 하우징/상호작용

현재 제품 흐름에서 고양이 획득 결과가 실제 보상 공간으로 이어지는지 검증한다.

```text
가챠로 USER_CATS 생성
→ 하우징/고양이 목록 진입
→ 내가 가진 고양이 조회
→ 고양이 선택
→ 상호작용/대화
```

## 확인

- 다른 사용자의 USER_CAT에 접근 불가
- CATS master 정보와 USER_CATS 소유권이 정상 결합
- 대화 시 `CAT_MEMORIES` 조회/갱신 정책 준수
- 외부 LLM 실패가 고양이 소유 데이터까지 rollback시키지 않음

LLM 호출은 장시간 DB transaction 안에 넣지 않는다.

---

# E2E-06. 배틀 방 생성 → 참가 → Ready → 시작

## 흐름

```text
방장 방 생성
→ 다른 사용자 방 목록 조회
→ 방 참가
→ Ready
→ 시작 조건 만족
→ 방장 Start
→ IN_PROGRESS
→ game_started WebSocket
```

## 확인

- 마지막 자리 동시 입장에도 max_participants 초과 없음
- 같은 사용자 중복 참가 없음
- 방장이 아닌 사용자는 Start 불가
- 시작 조건은 확정된 비즈니스 규칙 사용
- DB commit 후 WebSocket 전송
- socket이 끊겨도 snapshot으로 현재 상태 복구

---

# E2E-07. 배틀 문제 풀이 → 점수 → 종료 → 보상

## 흐름

```text
IN_PROGRESS
→ 참가자 문제 제출
→ 서버 채점
→ 정답이면 점수 반영
→ score_changed broadcast
→ 종료 조건 충족
→ FINISHED
→ 결과 계산
→ 배틀 보상
```

## 반드시 확인할 문제

현재 ERD만으로:

```text
이 사용자가 이 방의 이 문제에서 이미 점수를 받았는가?
```

를 영속적으로 기록하는 구조가 충분한지 검토가 필요하다.

중복 득점 방어가 확정되지 않은 상태에서는 배틀 점수 기능을 완료 처리하지 않는다.

## 보상

- 결과 보상은 한 번만 지급
- finish 재호출로 추가 지급되지 않음
- 보상 지급 실패 시 room 결과와 transaction 경계를 명확히 함

---

# E2E-08. 배틀 중 연결 끊김 → 재접속

## 흐름

```text
게임 진행
→ 사용자 WebSocket 끊김
→ DB에는 room/participant/score 유지
→ 사용자 재접속
→ JWT 확인
→ 참가자 확인
→ room snapshot 복구
→ socket 재구독
```

## 확인

- 점수가 초기화되지 않음
- Ready/room status 일치
- FINISHED였다면 게임 화면이 아니라 결과 화면으로 이동
- 메모리 connection registry가 게임 상태의 유일한 기준이 아님

---

# E2E-09. 랭킹 확인 → 승급전 시작 → 코드 저장

## 흐름

```text
랭킹 화면
→ 그룹 참가 상태 확인
→ 승급전 도전
→ RANK_CHALLENGES 생성
→ RANK_CHALLENGE_TASKS 생성
→ 문제 풀이
→ saved_code 자동 저장
```

## 확인

- challenge와 challenge tasks가 같은 시작 transaction에서 생성
- active challenge 중복 생성 방지
- 문제 순서 고정
- expires_at 서버 기준 판정
- 재접속 후 saved_code 복원

문제 수/제한시간은 확정 규칙을 사용한다.

---

# E2E-10. 승급전 성공 → 랭크 점수/보상

## 흐름

```text
모든 합격 조건 충족
→ IN_PROGRESS → SUCCESS
→ ranking score 반영
→ 성공 보상 지급
→ 결과 화면
```

## 확인

- SUCCESS 최초 전환에서만 보상
- 완료 로직 재호출 시 중복 보상 없음
- 만료 후 성공 처리되지 않음
- 점수와 보상 중 하나만 저장되는 반쪽 성공 방지

실패/점수 감소 정책은 기획 확정값을 따른다.

---

# E2E-11. 승급전 도중 서버 재시작

## 흐름

```text
challenge IN_PROGRESS
→ 서버 재시작
→ DB에 started_at/expires_at/saved_code 유지
→ 다시 접속
→ server now와 expires_at 비교
```

## 경우 A: 아직 만료 전

이어하기 허용 정책이면 saved_code를 복구한다.

## 경우 B: 이미 만료

```text
IN_PROGRESS → TIMEOUT
```

으로 확정한다.

프론트 카운트다운 값만 믿지 않는다.

---

# E2E-12. BackgroundTask 유실

## 흐름

```text
POST /attempts
→ PENDING commit
→ 서버 프로세스 종료
→ BackgroundTask 유실
→ 서버 재시작
```

## 확인

- PENDING이 영원히 남지 않음
- stale 정책으로 SYSTEM_ERROR 전환 가능
- 사용자가 새 attempt 제출 가능
- 보상/숙련도는 잘못 반영되지 않음

---

# E2E-13. 재화 transaction 실패

상점/가챠/출석 등에서 중간 오류를 강제로 만든다.

## 출석

```text
attendance INSERT 성공
→ balance UPDATE 실패
→ 전체 rollback
```

## 상점

```text
balance 차감
→ inventory 저장 실패
→ 전체 rollback
```

## 가챠

```text
재화 차감
→ USER_CATS 저장 실패
→ 전체 rollback
```

사용자가 손해만 보는 반쪽 transaction이 없어야 한다.

---

# E2E-14. JWT 도입 후 user_id 위조

## 공격 예

로그인 사용자가 Request body/path에 다른 사용자 UUID를 넣는다.

## 확인

최종 인증 API는:

```text
JWT user_id
```

를 기준으로 본인 자산을 수정한다.

다른 사용자의:

- balance
- inventory
- house
- cats
- attempts
- attendance

를 임의로 변경할 수 없어야 한다.

---

# E2E-15. 관리자 마스터데이터 변경 영향

## 예: TASK 비활성화

```text
admin이 TASK is_active=false
→ 새 학습 목록에서 제외
→ 기존 TASK_ATTEMPTS 기록은 유지
```

## 예: ITEM 가격 변경

```text
관리자 가격 변경
→ 이후 새 구매는 새 가격
→ 기존 Inventory는 유지
```

## 확인

- 일반 user는 관리자 API 거절
- 참조 중 데이터 물리삭제로 과거 기록이 깨지지 않음
- `test_cases`는 일반 사용자에게 노출되지 않음

---

# 통합 테스트 실행 순서 추천

처음부터 모든 E2E를 한 번에 돌릴 필요는 없다.

```text
1. 인증/사용자/출석
2. 학습 조회/제출
3. Docker 채점
4. 보상/상점
5. 하우징
6. 가챠/고양이
7. 배틀 lobby
8. 배틀 scoring/WebSocket
9. 승급전
10. 장애 복구/동시성
```

앞 단계의 데이터가 뒤 단계 테스트에 재사용될 수 있다.

---

# 테스트 기록 양식

```text
E2E ID:
시작 사용자/DB 상태:
호출 순서:
각 API Status:
중간 DB 변화:
최종 DB 변화:
WebSocket 이벤트:
예상 결과:
실제 결과:
PASS / FAIL:
```

---

# 완료 기준

E2E 테스트는 단순히 마지막 화면이 보이는지만 확인하지 않는다.

```text
API Response
+ DB 최종 상태
+ transaction rollback
+ 중복 방어
+ 실시간 이벤트
```

를 함께 본다.

각 도메인이 따로 정상인 것을 넘어, 최신 제품 흐름인:

```text
학습 / 배틀 / 승급전
→ 보상
→ 재화
→ 상점 / 가챠
→ 하우징 / 고양이
```

가 실제로 끊기지 않고 이어져야 백엔드 통합이 완료됐다고 볼 수 있다.