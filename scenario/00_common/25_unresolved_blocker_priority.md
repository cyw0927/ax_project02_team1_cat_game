# 미정사항 우선순위와 개발 블로커

이 문서는 현재 프로젝트에서 아직 확정되지 않은 규칙 중 **무엇을 먼저 결정해야 실제 개발이 막히지 않는지** 우선순위를 매긴다.

중요한 기준은 다음과 같다.

```text
P0 = 이걸 안 정하면 핵심 구현을 시작하거나 마무리하기 어려움
P1 = 구현은 가능하지만 곧 수정 가능성이 큼
P2 = MVP 이후로 미뤄도 됨
```

---

# P0. 가장 먼저 결정해야 하는 것

## 1. TASKS.test_cases 저장 형식

영향:
- 일반 학습 채점
- 배틀 문제 채점
- 승급전 채점
- Docker executor 입력 형식

결정 필요:
- JSON 문자열인지
- function mode인지 stdout mode인지
- entrypoint를 어떻게 지정하는지
- args/expected 구조

추천 MVP:

```json
{
  "mode": "function",
  "entrypoint": "add",
  "cases": [
    {"args": [1, 2], "expected": 3}
  ]
}
```

이 규칙이 안 정해지면 Docker는 실행돼도 **무엇을 테스트해야 하는지** 확정할 수 없다.

---

## 2. TASK_ATTEMPTS 최종 상태값

결정 필요:

```text
PENDING
RUNNING
PASSED
WRONG_ANSWER
RUNTIME_ERROR
TIMEOUT
SYSTEM_ERROR
```

정도로 나눌지.

영향:
- DB 저장
- polling Response
- 프론트 결과 화면
- 테스트

---

## 3. 채점 결과 메시지 저장 여부

현재 TASK_ATTEMPTS에는:

```text
result_message
stderr
```

같은 컬럼이 없다.

사용자가 나중에 polling으로 RUNTIME_ERROR 내용을 다시 보려면 저장 위치가 필요하다.

결정:
- 컬럼 추가
- 최종 결과 조회 시 메모리/별도 저장
- 상세 오류는 저장하지 않음

추천은 nullable `result_message` 같은 최소 컬럼 검토.

---

## 4. 학습 보상 중복 지급 규칙

결정 필요:
- 문제 최초 정답만 보상?
- 하루 최초 정답만 보상?
- 난이도별 일일 N회 제한?
- 힌트 사용 시 보상?

이 규칙은 USERS 재화와 직접 연결되므로 늦게 정하면 코드 재수정이 크다.

---

## 5. 재화 구조

현재 ERD:

```text
USERS.balance
USERS.mileage
```

기획 후보:
- 싼 재화(사료)
- 비싼 재화(금화)
- mileage

결정 필요:
- balance 하나로 갈지
- 사료/금화 컬럼을 나눌지
- mileage는 별도 유지할지

영향:
- 학습 보상
- 출석
- 배틀
- 승급전
- 상점
- 가챠

프로젝트 전체에 영향이 가장 큰 P0 항목 중 하나다.

---

## 6. 가챠 기본 규칙

최소한 아래는 정해야 API transaction을 완성할 수 있다.

```text
1회 비용
희귀도/결과 확률
중복 처리
USER_CATS 중복 row 허용 여부
마일리지 사용 여부
```

천장은 MVP에서 미룰 수 있지만 중복 정책은 미루기 어렵다.

---

## 7. 배틀 점수 규칙

결정 필요:
- 정답 시 점수
- 오답 감점 여부
- 재제출 허용
- 같은 문제 중복 득점 방지
- 개인전/팀전 점수 계산

`current_score`를 언제 어떻게 올리는지가 결정되지 않으면 실시간 배틀 핵심을 못 만든다.

---

## 8. 배틀 종료 조건과 보상 중복 방지

결정 필요:
- 모든 문제 종료?
- 제한시간 종료?
- 방장 종료?
- 보상 1회 지급 사실을 어디에 저장?

현재 ERD에는 `reward_claimed` 같은 필드가 없다.

배틀 보상을 넣으려면 이 부분은 반드시 해결해야 한다.

---

## 9. 승급전 합격 조건

결정 필요:
- 문제 수
- 제한시간
- 몇 문제 맞으면 성공인지
- 실패 시 rank score 감소 여부
- 성공 시 score 증가량

현재 `expires_at`과 status는 있지만 실제 합격 계산 규칙이 없다.

---

## 10. 인증 방식과 USERS 스키마

현재 USERS에는 password/hash/email이 없다.

결정 필요:
- username + password
- 소셜 로그인
- password_hash 컬럼
- username UNIQUE
- JWT access/refresh 정책

인증은 마지막에 붙일 수 있지만 USERS migration은 다른 기능과 충돌할 수 있어 설계는 미리 결정하는 편이 좋다.

---

# P1. 구현 도중 확정해도 되는 것

## 11. 문제 title / description

현재 TASKS에 문제 지문 저장 컬럼이 부족하다.

문제 화면 완성 전에 결정하면 된다.

추천:

```text
title
description
```

---

## 12. Docker 실행 timeout

자원 제한 자체는 확정:

```text
128MB
CPU 0.5
network none
read-only
```

정확한 실행시간 초 단위만 정하면 된다.

---

## 13. Docker 출력 크기 제한

사용자가 무한 print를 하는 경우 로그가 커질 수 있다.

MVP라도 적당한 output cap이 필요하다.

---

## 14. 방 시작 규칙

결정:
- 최소 인원
- 전원 Ready 여부
- 방장도 Ready 여부
- 방장 자동 participant 여부

방 join API는 먼저 만들 수 있지만 start 완성 전에 필요하다.

---

## 15. 하우징 position_data 스키마

현재 JSONB라 유연하지만 너무 자유롭다.

결정 후보:

```json
{"x": 2, "y": 3, "rotation": 90}
```

- 좌표 범위
- rotation 값
- 충돌 서버 검사 여부

---

## 16. 출석 시간대

`date.today()`를 그대로 쓸지, 한국시간 기준으로 명확히 고정할지.

서비스가 한국 교육 프로젝트라면 KST 기준이 이해하기 쉽다.

---

# P2. MVP 후에도 가능한 것

## 17. 가챠 천장

핵심 가챠가 먼저 돌아간 뒤 추가 가능.

다만 천장을 넣는다면 누적 횟수 저장 위치가 필요하다.

---

## 18. 고양이 메모리 고도화

- 몇 대화마다 요약?
- 기억 몇 개 유지?
- 장기/단기 메모리 분리?

MVP에서는 context_summary 하나로도 충분.

---

## 19. 하우징 충돌 판정 정교화

MVP는 프론트 배치 UX 위주로 두고 서버는 범위/소유권 정도만 검증 가능.

---

## 20. 랭킹 시즌제

현재 ERD는 지속 점수 중심이다.

주간/시즌 초기화는 별도 설계가 필요하므로 후순위.

---

# 결정 회의 추천 순서

팀 회의에서는 한 번에 전부 정하려 하지 말고 아래 순서로 가면 된다.

```text
1. test_cases
2. 채점 status
3. 학습 보상
4. 재화 구조
5. 가챠
6. 배틀 점수/종료
7. 승급전
8. 인증
9. 하우징 세부
```

# 누가 결정해야 하나

| 항목 | 주도 |
| --- | --- |
| UX/보상/확률/점수 | 기획 + 팀 합의 |
| API Request/Response | 프론트 + 백엔드 |
| transaction/lock | 백엔드 |
| Docker 자원/timeout | 백엔드 |
| DB 컬럼/constraint | 백엔드 3명 공동 |
| JWT 사용 방식 | 백엔드 + 프론트 |

# 핵심 원칙

미정값을 코드에 임시 숫자로 넣고 나중에 기억에 의존해서 고치지 않는다.

정말 임시값이 필요하다면:

```text
TODO: BUSINESS_RULE_NOT_FINAL
```

처럼 명시하거나 설정값으로 분리한다.

특히 재화, 확률, 점수는 하드코딩 전에 반드시 문서에서 확정한다.
