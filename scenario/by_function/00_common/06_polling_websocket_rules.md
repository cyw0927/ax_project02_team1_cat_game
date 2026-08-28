# Polling과 WebSocket 사용 기준

실시간처럼 보이는 기능이라고 모두 WebSocket을 쓸 필요는 없다. 구현 복잡도와 필요한 반응 속도를 보고 나눈다.

## 1. 문제 채점 결과: Polling 추천

문제 제출 후 사용자는 몇 초 내에 결과를 한 번 받으면 된다.

```text
POST /attempts
→ 202 + attempt_id
→ 1초 정도 간격으로 GET /attempts/{attempt_id}
→ PENDING/RUNNING이면 계속 기다림
→ 최종 상태가 되면 polling 종료
```

### 왜 polling이 좋은가

- 구현이 단순하다.
- 재연결 처리가 쉽다.
- Swagger로 확인하기 쉽다.
- 채점 하나 때문에 WebSocket 연결을 계속 유지할 필요가 없다.

### 주의

polling 간격을 너무 짧게 잡으면 서버에 불필요한 요청이 많아진다. 정확한 간격은 프론트와 합의한다.

---

## 2. 실시간 배틀: WebSocket 추천

배틀에서는 참가자의 준비 상태와 점수가 즉시 여러 사용자에게 전달되어야 한다.

예:

```text
A가 정답
→ 서버 current_score 갱신
→ 같은 room WebSocket 참가자에게 score_update broadcast
→ 모든 화면 점수판 갱신
```

이런 이벤트를 매번 polling으로 처리하면 참가자마다 계속 방 상태를 조회해야 하므로 비효율적이고 반응도 느릴 수 있다.

## 3. WebSocket 이벤트 예시

아직 최종 계약은 아니지만 이벤트를 문자열로 구분하면 이해하기 쉽다.

```json
{
  "type": "score_update",
  "user_id": "uuid",
  "score": 300
}
```

다른 후보:

```text
participant_joined
participant_left
ready_changed
battle_started
score_update
battle_finished
```

이 이벤트 이름은 프론트/백엔드 합의 후 고정한다.

## 4. DB가 진짜 상태의 기준

WebSocket 메시지만 믿고 점수를 관리하면 안 된다.

```text
DB current_score = 실제 상태
WebSocket = 그 상태가 바뀌었다고 화면에 알려주는 전달 수단
```

사용자가 재접속하면 DB에서 최신 상태를 다시 조회하고 WebSocket에 재연결할 수 있어야 한다.

## 5. 연결이 끊겼을 때

다음 정책을 배틀 시나리오에서 확정해야 한다.

- 연결이 끊겨도 참가자 row를 바로 삭제할지
- 몇 초/분 동안 재접속을 허용할지
- 재접속 시 기존 score를 유지할지
- 완전히 이탈한 사용자의 팀 점수를 어떻게 할지

## 6. 초보자용 구분

```text
결과 하나를 조금 뒤에 받으면 됨
→ Polling

여러 사람이 같은 변화를 즉시 받아야 함
→ WebSocket
```

따라서 현재 추천은:

```text
학습 채점 → Polling
승급전 채점 → Polling 또는 일반 HTTP 흐름
실시간 배틀 상태/점수 → WebSocket
상점/출석/가챠 → 일반 HTTP
```