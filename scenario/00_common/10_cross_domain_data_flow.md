# 도메인 간 데이터 흐름

폴더는 기능별로 분리되어 있지만 실제 사용자는 여러 도메인을 연속해서 이용한다.

이 문서는 최신 제품 흐름을 기준으로 **어느 도메인이 무엇을 결정하고, 다음 도메인에 어떤 데이터를 넘기는지** 정리한다.

상위 제품 흐름은 `13_latest_product_flow.md`를 기준으로 한다.

---

# 1. 로그인 → 자동 출석 → 홈

확정된 출석 흐름:

```text
인증 성공
→ users/auth가 current_user 식별
→ attendance service 실행
→ 서버 기준 오늘 날짜 계산
→ ATTENDANCES INSERT 시도
→ 오늘 첫 출석이면 USERS.balance + 100
→ 이미 오늘 출석이면 추가 지급 없음
→ 로그인 정상 완료
→ 홈
```

책임 분리:

- `auth`: 사용자가 누구인지 확인
- `users/attendance`: 오늘 출석과 streak, 100원 지급 transaction
- frontend: 새 보상 여부를 받아 팝업/UI 표시

같은 날 출석 중복이 발생했다고 로그인 자체가 실패하면 안 된다.

서비스 기준 timezone 값은 아직 팀 결정사항이다.

---

# 2. 학습 → 채점 → 보상 → 재화

```text
문제 선택
→ learning이 TASKS 조회
→ 코드 제출
→ TASK_ATTEMPTS PENDING 저장
→ BackgroundTask
→ sandbox 채점
→ learning이 최종 결과 확정
→ 보상 자격 확인
→ USERS 재화 증가
```

책임:

- `learning`: 문제/시도/정답 여부
- `sandbox`: 격리된 Python 실행
- `users/economy`: 실제 재화 값 정합성

Docker가 정답 보상량을 결정하지 않는다.

배틀이나 승급전 제출을 일반 학습 제출로 간주해 학습 보상까지 자동 지급할지는 별도 규칙이다.

---

# 3. 재화 → 상점 → Inventory → 하우징

```text
상점 진입
→ ITEMS 조회
→ 구매
→ 서버 가격 기준 재화 Atomic 차감
→ INVENTORIES quantity 증가
→ 하우징 진입
→ Inventory 소유 확인
→ PLACED_OBJECTS 배치
```

책임:

- `economy/shop`: 가격, 구매, 재화 차감, Inventory
- `housing`: 소유한 item을 실제 공간에 적용

하우징은 가격을 다시 계산하지 않는다.

아이템을 하우스에서 치워도 Inventory 소유권은 사라지지 않는다.

---

# 4. 재화 → 가챠 → 고양이 → 하우징

```text
가챠 요청
→ 서버 비용 확인
→ 재화 Atomic 차감
→ 서버 확률/규칙으로 결과 결정
→ USER_CATS 반영 또는 확정된 중복 정책 처리
→ 하우징/고양이 화면에서 보유 결과 확인
```

책임:

- 가챠 로직: 비용/확률/결과 transaction
- `cats`: CATS master, USER_CATS ownership, CAT_MEMORIES
- `housing`: 고양이를 공간에서 어떻게 보여줄지

현재 ERD에는 `USER_CATS`의 하우징 위치 저장 방식이 확정되어 있지 않다.

따라서:

```text
가챠 결과 저장
```

과

```text
하우징에서 고양이 배치/자동이동 표현
```

은 별도 결정으로 본다.

---

# 5. 배틀 Lobby → 채점 → 점수 → 결과 → 보상

```text
방 생성/참가
→ Ready
→ Start
→ ROOM_TASKS 문제 풀이
→ sandbox 채점
→ 서버 점수 규칙 적용
→ ROOM_PARTICIPANTS.current_score 변경
→ commit
→ WebSocket score_changed
→ 종료 조건
→ 결과 확정
→ 결과 보상
```

책임:

- `battle`: room 상태, participant, 점수, 결과
- `learning/TASKS + sandbox`: 문제와 실행 기반 채점 재사용 가능
- `economy/users`: 확정된 배틀 보상 재화 write
- WebSocket: DB에 확정된 상태를 실시간 전달

중요:

```text
WebSocket = 진실의 저장소 아님
DB = 최종 상태 기준
```

현재 ERD는 `사용자-방-문제별 이미 득점했는가`를 영속적으로 기록하는 방법이 부족하므로 scoring 구현 전에 데이터 구조를 확정해야 한다.

---

# 6. 랭킹 → 승급전 → 채점 → 성공/실패 → 보상

```text
랭킹 조회
→ 승급전 시작
→ RANK_CHALLENGES / RANK_CHALLENGE_TASKS 생성
→ 코드 저장/문제 풀이
→ sandbox 채점
→ is_passed 변경
→ 전체 합격조건 확인
→ SUCCESS / FAILED / TIMEOUT
→ rank score 변경
→ SUCCESS 보상
```

책임:

- `ranking`: challenge 상태, task 순서, 만료, rank score
- `sandbox`: 코드 실행
- `economy/users`: 확정된 성공 보상 재화 write

`expires_at` 최종 판정은 서버 시간이 한다.

SUCCESS/보상은 재처리되어도 한 번만 반영되어야 한다.

---

# 7. 고양이 상호작용 → 기억

```text
하우징/고양이 화면
→ USER_CAT 선택
→ ownership 확인
→ CATS.persona 조회
→ CAT_MEMORIES 조회
→ 외부 LLM 호출
→ 필요한 경우 context_summary 갱신
```

긴 LLM 호출 중 DB transaction을 계속 열어두지 않는다.

다른 사용자의 USER_CAT memory를 수정할 수 없어야 한다.

---

# 8. 인증 → 모든 사용자 write

현재 일부 API는 path/body에 `user_id`를 직접 받는 임시 구조다.

최종 방향:

```text
JWT
→ current_user
→ 서버가 실제 사용자 ID 결정
```

대상:

- 학습 제출/이력
- 상점 구매/Inventory
- 가챠
- 내 하우스 수정
- 출석
- 배틀 Ready/Start/submit
- 승급전
- 고양이 대화

프론트가 보낸 다른 사용자 UUID만 믿고 자산을 변경하지 않는다.

공개 조회 기능과 본인 write 기능은 구분한다.

예:

```text
다른 사용자의 공개 하우스 GET → 가능 정책
다른 사용자의 하우스 PATCH → 금지
```

---

# 9. 공유 테이블과 코드 책임은 다르다

`USERS`를 여러 도메인이 사용한다고 users 폴더가 모든 기능을 맡는 것은 아니다.

```text
USERS.balance
→ 상점 차감은 economy
→ 출석 증가는 attendance
→ 학습 보상은 learning 결과에서 시작
→ 배틀/승급전 보상은 각 결과에서 시작
```

```text
USERS.wallpaper_item_id
→ 실제 변경 로직은 housing
```

DB 컬럼 위치와 비즈니스 로직 소유권을 구분한다.

---

# 10. transaction 경계

한 요청이 여러 테이블을 변경하면 **반쪽 성공**이 없어야 한다.

대표 예:

```text
출석 INSERT + 100원 증가
상점 balance 차감 + Inventory 증가
가챠 재화 차감 + USER_CATS/중복보상
승급전 SUCCESS + rank score + 성공보상
```

반대로 긴 작업은 transaction 밖에서 실행한다.

```text
Docker 실행
LLM 호출
WebSocket broadcast
긴 sleep/polling
```

원칙:

```text
긴 외부/실행 작업 완료
→ 짧은 DB transaction
→ COMMIT
→ 필요한 WebSocket 전송
```

---

# 11. 전체 연결도

```text
로그인
 └→ 자동 출석 → 재화
      ↓
     홈
      ├→ 학습 ──────→ sandbox → 결과 → 보상 ─┐
      ├→ 배틀 ──────→ sandbox → 점수/결과 → 보상 ─┤
      └→ 승급전 ────→ sandbox → 성공/실패 → 보상 ─┤
                                                  ↓
                                                 재화
                               ┌──────────────────┴─────────────────┐
                               ↓                                    ↓
                              상점                                 가챠
                               ↓                                    ↓
                           Inventory                             UserCats
                               └──────────────→ 하우징 ←────────────┘
                                                    ↓
                                              고양이 상호작용
                                                    ↓
                                               CatMemory/LLM
```

이 연결을 기준으로 새 기능이 어느 도메인의 책임인지, 어느 transaction에서 다른 테이블까지 바꾸는지 판단한다.

---

# 12. 최종 원칙

- 같은 규칙을 여러 router에 복사하지 않는다.
- 프론트가 보내는 가격/보상/점수/현재시간을 신뢰하지 않는다.
- DB가 최종 상태의 기준이다.
- 재화 write는 exactly-once/중복 방어를 고려한다.
- 미정 비즈니스 규칙을 도메인 연결 문서가 임의로 확정하지 않는다.
- 제품 흐름이 바뀌면 먼저 `13_latest_product_flow.md`를 갱신하고 이 문서를 같이 맞춘다.