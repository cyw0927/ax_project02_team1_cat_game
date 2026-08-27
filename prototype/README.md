# 플레이어블 프로토타입

현재 실행 진입점은 `prototype/index.html`이며 최신 버전은 `playable_mockup_v4.html`입니다.

## 실행 방법

### 1. FastAPI 서버

```powershell
cd server
.\.venv\Scripts\Activate.ps1
uvicorn app.main:app --reload
```

기본 API 주소는 `http://127.0.0.1:8000`입니다.

### 2. 프로토타입 정적 서버

새 터미널에서:

```powershell
cd prototype
python -m http.server 5500
```

브라우저에서:

```text
http://127.0.0.1:5500/
```

`index.html`이 최신 플레이어블 버전을 자동으로 로드합니다.

## 현재 실제 FastAPI 연결

### 학습

- `GET /` 서버 상태 확인
- `GET /tasks` 활성 문제 목록 조회
- 실제 DB에 존재하는 사용자 UUID를 입력한 경우 `POST /attempts`
- 제출 성공 시 실제 `attempt_id`와 `PENDING` 상태 표시

현재 백엔드의 채점 worker가 아직 학습 라우터에 연결되지 않았기 때문에 `POST /attempts` 이후 결과가 `PENDING`에 머무를 수 있습니다. 이 상태를 정답으로 가장하거나 DEMO 보상을 지급하지 않습니다.

### 상점

- `GET /items` 실제 아이템 목록 조회
- `POST /shop/buy` 실제 구매
- `GET /users/{user_id}/inventory` 실제 인벤토리 조회
- 구매 성공 시 서버가 반환한 실제 DB 잔액과 보유 수량 표시
- 잔액 부족, 사용자 없음, 아이템 없음 등의 서버 오류를 그대로 표시

상점의 실제 DB 재화와 홈 화면의 DEMO 사료 숫자는 서로 섞지 않습니다.

프로토타입은 `5500`, FastAPI는 `8000`에서 실행되므로 개발용 CORS 허용 목록에 `localhost:5500`과 `127.0.0.1:5500`이 등록되어 있습니다.

## 아직 DEMO인 기능

- 학습 정답 보상/재화 증가
- 데일리 퀘스트
- 가챠 소비와 결과
- 가챠로 획득한 고양이 목록 공유

이 값들은 플레이 흐름 검증용이며 실제 서비스 경제 규칙이 아닙니다.

## 하우스 프로토타입

- A* 이동 경로 탐색
- 가구 충돌 회피
- 깊이에 따른 캐릭터 크기 조절
- 자동 산책과 IDLE 행동
- 소파 → 앉기
- 침대 → 자기
- 공부 지점 → 공부 행동
- 고양이 클릭 → 말풍선 반응

## 권장 검증 순서

1. FastAPI와 prototype 서버를 둘 다 실행합니다.
2. 홈에서 `Study`로 이동합니다.
3. `FastAPI 연결됨` 표시와 실제 `/tasks` 개수를 확인합니다.
4. DBeaver 등에서 실제 USERS 테이블의 UUID 하나를 입력합니다.
5. 코드를 제출합니다.
6. 화면에 실제 `attempt_id`와 `status=PENDING`이 표시되는지 확인합니다.
7. DB의 `TASK_ATTEMPTS`에 같은 attempt가 생성됐는지 확인합니다.
8. 홈에서 `Shop`으로 이동합니다.
9. 같은 실제 사용자 UUID로 아이템 목록을 불러오고 구매합니다.
10. 화면의 실제 DB 잔액과 인벤토리 수량이 바뀌는지 확인합니다.
11. DBeaver에서 USERS.balance와 INVENTORIES가 같은 결과인지 확인합니다.
12. Home/Daily/Gacha/House DEMO 흐름도 기존처럼 동작하는지 회귀 확인합니다.
13. House에서 이동과 가구 상호작용을 확인합니다.

## 파일 관계

```text
index.html
└─ playable_mockup_v4.html          # FastAPI 상점 연결
   └─ playable_mockup_v3.html       # FastAPI 학습 연결
      └─ playable_mockup_v2.html    # 공유 DEMO 게임 상태
         └─ house_motion_mockup_v4.html
            └─ house_motion_mockup_v3.html
               └─ house_motion_mockup_v2.html
                  └─ house_motion_mockup.html
```

이전 버전은 회귀 확인용으로 유지합니다. 평소에는 `index.html`만 실행하면 됩니다.

## 다음 실제 API 교체 순서

1. 학습 `PENDING` → Docker 채점 결과 연결
2. 실제 사용자 식별 방식/JWT 연결
3. 하우징 API 연결
4. 가챠 정책 확정 후 가챠 API 연결
