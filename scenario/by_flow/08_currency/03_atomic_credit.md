# 03. 재화 원자 증가

## 목적
동시에 여러 보상이 들어와도 재화가 누락되거나 덮어써지지 않게 DB에서 원자적으로 증가시킨다.

## 정상 흐름
1. 보상 자격과 중복 여부가 확정된다.
2. 짧은 transaction 안에서 재화 증가를 실행한다.
3. 필요한 지급 기록과 함께 commit한다.
4. 최신 잔액을 반환한다.

## 권장 형태
```sql
UPDATE users
SET balance = balance + :reward
WHERE id = :user_id;
```

Python에서 기존 balance를 읽고 계산한 값을 다시 저장하는 read-modify-write 방식은 피한다.

## 발생 가능한 변수
### A. 학습 보상과 배틀 보상이 동시에 들어옴
- 원자 증가라면 둘 다 반영 가능하다.
- read-modify-write라면 한쪽 증가분이 사라질 수 있다.

### B. 지급 기록 저장은 성공했지만 balance 증가 실패
- 해결: 둘을 같은 짧은 transaction으로 묶고 하나라도 실패하면 rollback한다.

### C. balance 증가 후 응답 유실
- 재요청 시 02단계 멱등성 검증을 통해 두 번째 지급을 막는다.

### D. 잘못된 음수 reward
- 서버가 허용된 보상 규칙을 확인하고 증가 API에 임의 음수가 들어가지 않게 검증한다.

## DB/락 원칙
- 불필요한 `FOR UPDATE`를 사용하지 않는다.
- 단순 증감은 원자 UPDATE 우선.
- 장시간 외부 작업과 같은 transaction을 공유하지 않는다.

## UI
- 서버 commit 전에는 잔액을 확정값처럼 표시하지 않는다.
- 성공 응답의 최신 잔액으로 화면을 갱신한다.

## 다음 단계
`04_concurrent_credit.md`

## 테스트
- 보상 1회
- 두 보상 동시 발생
- 세 기능 동시 보상
- transaction 중 오류
- 응답 유실 후 재조회

## TBD
- balance 외 추가 재화 필드의 동일 처리 방식