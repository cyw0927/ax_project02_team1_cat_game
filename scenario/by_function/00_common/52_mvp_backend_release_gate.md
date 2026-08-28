# MVP 백엔드 릴리즈 게이트

이 문서는 기능 문서가 많이 쌓여도 **어느 수준까지 가야 MVP 백엔드를 실제로 연결 가능한 상태라고 볼지** 마지막 점검 기준을 정리한다.

모든 아이디어를 다 구현해야 MVP가 되는 것은 아니다.

반대로 endpoint가 몇 개 실행된다고 MVP가 끝난 것도 아니다.

---

# 1. 공통 서버

릴리즈 전 최소:

```text
[ ] 서버가 깨끗한 환경에서 실행됨
[ ] DB 연결 성공
[ ] Alembic head 일치
[ ] GET / 정상
[ ] /docs 정상
[ ] .env 비밀값이 Git에 없음
[ ] 주요 오류가 traceback 그대로 사용자에게 노출되지 않음
```

---

# 2. 인증

최신 흐름이 로그인에서 시작하므로 실제 통합 MVP에서는 사용자 식별 방식이 필요하다.

```text
[ ] 로그인 방식 확정
[ ] 사용자 식별이 서버에서 신뢰 가능
[ ] JWT를 사용한다면 토큰 검증 동작
[ ] 다른 user_id를 넣어 타인 자산 수정 불가
[ ] 관리자 기능이 있다면 role 403 동작
```

인증을 발표용 mock으로 제외한다면 어떤 endpoint가 임시 user_id 기반인지 명확히 적어야 한다.

---

# 3. 자동 출석

확정 요구사항:

```text
매일 자정 이후 첫 로그인
→ 출석 1회
→ 100 지급
```

게이트:

```text
[ ] 첫 로그인에서 자동 처리
[ ] 같은 날 두 번째 로그인은 추가 지급 없음
[ ] ATTENDANCES(user_id,date) UNIQUE 동작
[ ] 출석 + 보상 같은 transaction
[ ] 중간 실패 rollback
[ ] 서비스 timezone 확정/테스트
[ ] 클라이언트 날짜를 믿지 않음
```

---

# 4. 학습 핵심 루프

최신 흐름:

```text
문제 선택
→ 코드 작성
→ 제출
→ 채점
→ 정답 보상
→ 재화 획득
```

게이트:

```text
[ ] 문제 목록/상세 조회
[ ] test_cases 비노출
[ ] POST /attempts가 202 + PENDING 반환
[ ] BackgroundTask 연결
[ ] Docker executor 연결
[ ] CPU 0.5 / memory 128MB / network none / read-only
[ ] 실행 timeout/output cap
[ ] 실제 결과 상태 저장
[ ] polling 종료 가능
[ ] RuntimeError/Timeout/SystemError 구분
[ ] 컨테이너 cleanup
[ ] 정답 보상 중복 방어
[ ] 재제출 정상
```

이 흐름이 끊기면 학습 MVP는 완료가 아니다.

---

# 5. 경제·상점

```text
[ ] 서버 ITEM 가격 기준 구매
[ ] 잔액 부족 방어
[ ] Atomic UPDATE
[ ] Inventory upsert
[ ] 차감 + 지급 same transaction
[ ] 실패 rollback
[ ] 최종 잔액 Response 일치
```

재화가 2종 이상으로 확정되면 이 체크리스트를 실제 재화 컬럼 기준으로 다시 맞춘다.

---

# 6. 가챠·고양이

최신 흐름에서 가챠는 소비 루프의 핵심이다.

```text
[ ] 가챠 비용 확정
[ ] 결과 확률/선정 방식 서버 기준
[ ] 재화 Atomic 차감
[ ] USER_CATS 저장
[ ] 차감 + 결과 저장 같은 transaction
[ ] 저장 실패 rollback
[ ] 중복 고양이 정책 확정
[ ] 결과 Response로 프론트 연출 가능
```

천장/복잡한 이벤트는 MVP 이후로 미룰 수 있다.

하지만 **돈만 빠지고 고양이가 없는 상태**는 허용하면 안 된다.

---

# 7. 하우징

```text
[ ] 내 하우스 조회
[ ] Inventory 기반 가구 배치
[ ] 이동/회전/삭제
[ ] wallpaper/floor 적용
[ ] 소유하지 않은 item 거절
[ ] 보유량 초과 배치 방어
[ ] position_data 최소 validation 확정
```

최신 흐름의 `고양이 → 하우징`이 발표 핵심이면 추가로:

```text
[ ] 고양이 배치/노출 방식 확정
[ ] USER_CATS와 하우징 연결
```

이 필요하다.

---

# 8. 배틀 Lobby

```text
[ ] 방 생성
[ ] 방 목록
[ ] 방 참가
[ ] 마지막 자리 concurrency 테스트
[ ] 중복 참가 방어
[ ] Ready
[ ] 방장 권한
[ ] 시작 조건 확정
[ ] ROOM_TASKS 고정
```

---

# 9. 배틀 실제 경기

최신 흐름:

```text
게임 시작
→ 문제 풀이
→ 점수 경쟁
→ 결과 보상
```

게이트:

```text
[ ] 배틀 코드 제출/채점
[ ] 점수는 서버 채점 결과 기준
[ ] 사용자-방-문제 중복 득점 방어
[ ] WebSocket score/start/finish 전달
[ ] DB commit 후 broadcast
[ ] 재접속 snapshot 복구
[ ] 종료 조건
[ ] 승자/순위 계산
[ ] 보상 1회 지급
[ ] finish 재호출 중복 보상 없음
```

특히 **중복 득점 기록 구조가 해결되지 않으면 scoring 완료 처리 금지.**

---

# 10. 랭킹·승급전

```text
[ ] 랭킹 조회
[ ] 승급전 시작
[ ] 문제 순서 고정
[ ] 제한시간 서버 기준
[ ] saved_code 저장/복구
[ ] 승급전 문제 채점
[ ] is_passed 반영
[ ] SUCCESS/FAILED/TIMEOUT
[ ] rank score 반영
[ ] 성공 보상 1회성
```

정확한 문제 수/시간/점수량은 확정된 기획값을 쓴다.

---

# 11. 고양이 상호작용

MVP 발표 범위에 AI 대화가 포함된다면:

```text
[ ] 내 USER_CAT ownership 확인
[ ] persona 사용
[ ] LLM timeout/error 처리
[ ] 긴 외부 호출을 DB transaction 밖에서 실행
[ ] CAT_MEMORIES 읽기/갱신
[ ] 다른 사용자의 고양이 기억 수정 불가
```

발표 MVP에서 제외한다면 미구현임을 명확히 한다.

---

# 12. 동시성 필수 테스트

최소:

```text
[ ] 출석 동시 요청 → 1회 지급
[ ] 상점 동시 구매 → 잔액 음수 없음
[ ] 마지막 방 자리 동시 join → 정원 초과 없음
[ ] Docker 동시 제출 → 설정 이상 컨테이너 실행 없음
[ ] 최초 정답 보상 동시 처리 → 중복 지급 없음
[ ] 배틀 동일 문제 동시 제출 → 중복 득점 없음
[ ] 배틀/승급전 완료 재처리 → 보상 중복 없음
```

---

# 13. 장애/복구

```text
[ ] Docker 예외에서 SYSTEM_ERROR 처리 가능
[ ] 컨테이너 cleanup
[ ] 오래된 PENDING/RUNNING 복구 규칙
[ ] 서버 재시작 후 승급전 expires_at 재판정
[ ] WebSocket 재접속 시 DB snapshot 복구
[ ] transaction 중간 실패 시 반쪽 데이터 없음
```

---

# 14. 보안

```text
[ ] test_cases 비노출
[ ] password/hash 비노출
[ ] JWT secret 비노출
[ ] .env commit 없음
[ ] 프론트가 보내는 price/reward/score 신뢰하지 않음
[ ] 타인 user_id 자산 수정 불가
[ ] 관리자 API role 검사
[ ] Docker network 차단
```

---

# 15. 프론트 연결

백엔드만 성공해도 통합은 끝이 아니다.

```text
[ ] Request/Response 계약 공유
[ ] status code 공유
[ ] 로딩/PENDING 처리
[ ] 오류 message 처리
[ ] 최종 balance/inventory/score를 Response로 동기화
[ ] WebSocket 이벤트명/payload 합의
```

---

# 16. 발표 전 E2E 최소 코스

다음 세 코스는 최소한 한 번 끝까지 통과하는 것이 좋다.

## 코스 A — 학습 소비 루프

```text
로그인
→ 자동 출석
→ 학습 문제 제출
→ Docker 정답
→ 재화 획득
→ 상점 구매
→ 하우징 배치
```

## 코스 B — 고양이 루프

```text
재화 획득
→ 가챠
→ USER_CATS 생성
→ 고양이 화면/하우징에서 확인
```

## 코스 C — 경쟁 루프

```text
배틀 방
→ 참가/Ready
→ 문제 풀이
→ 점수
→ 결과
```

승급전까지 MVP에 포함하면:

```text
랭킹
→ 승급전
→ 문제 풀이
→ 성공/실패
```

도 추가한다.

---

# 17. 최종 판정

다음 셋을 구분한다.

```text
IMPLEMENTED = 코드 존재
TESTED = 정상/예외/DB 변화 검증
RELEASE_READY = E2E + 동시성 + 보안 + rollback까지 핵심 위험 검증
```

endpoint가 있다는 이유만으로 `RELEASE_READY`라고 표시하지 않는다.

이 문서의 핵심 목적은 기능을 계속 늘리는 게 아니라 **어디에서 멈추고 통합·검증에 들어가야 하는지 명확하게 만드는 것**이다.
