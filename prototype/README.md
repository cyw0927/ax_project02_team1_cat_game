# 플레이어블 프로토타입

최신 실행 경로는 `index.html` → `game.html`인 단일 앱입니다. 과거 `playable_mockup_v1~v14.html`과 `house_motion_mockup*`은 비교용 legacy로 보존하지만 최신 앱에서는 iframe으로 불러오지 않습니다.

## 실행

```powershell
cd server
.\.venv\Scripts\Activate.ps1
uvicorn app.main:app --reload
```

별도 터미널에서:

```powershell
cd prototype
python -m http.server 5500
```

브라우저에서 `http://127.0.0.1:5500/`을 엽니다. 우측 아래 톱니바퀴의 Debug 창에서 API 주소와 사용자 UUID를 입력할 수 있습니다. 개발 정보는 기본 게임 화면에 노출되지 않습니다.

## 구조

```text
prototype/
├─ index.html                 # game.html 진입점
├─ game.html                  # 모든 게임 화면의 단일 DOM
├─ css/game.css               # 게임 UI와 행동 표현
├─ js/api.js                  # FastAPI 요청
├─ js/state.js                # 사용자·게임 상태
├─ js/navigation.js           # 화면 전환과 기능 연결
├─ js/cat.js                  # cat_id 자산 매핑과 생성
├─ js/movement.js             # 가속·감속·전환·회피
└─ assets/                    # 기존 하우스/고양이 자산
```

홈에서 `일일 미션 / 학습 / 배틀 / 랭킹·승급전 / 하우징 / 상점 / 가챠` 7개 화면으로 직접 이동합니다. 일일 미션은 일반 학습과 분리되어 있습니다.

## 실제 FastAPI 연결

- 학습: `GET /tasks`, `POST /attempts` (`GET /attempts/{attempt_id}` 함수 포함)
- 상점: `GET /items`, `POST /shop/buy`
- 인벤토리: `GET /users/{user_id}/inventory` 함수 포함
- 하우징: 조회, 가구 배치/이동/삭제, wallpaper/floor 적용 함수 포함
- 보유 고양이: `GET /users/{user_id}/cats`
- 스타터: `POST /users/{user_id}/cats/starter`
- 사용자 재화: `GET /users/{user_id}`

UUID가 없으면 로컬 스타터 주황 고양이 한 마리를 즉시 표시합니다. UUID를 연결하면 스타터를 최소 1마리 보장한 뒤 실제 `USER_CATS` 결과로 교체합니다. `cat_id=1`은 주황, `2`는 검정, `3`은 흰색이며 그 외는 주황 자산으로 fallback합니다.

고양이는 가속 → 순항 → 감속으로 이동하고, 반대 방향 전환 전에 감속합니다. 목표 방향 보간과 고양이 간 분리 힘으로 경로와 겹침을 완화하며 IDLE 호흡·눈깜빡임도 표현합니다. 확보되지 않은 4방향·행동 스프라이트는 만들지 않았습니다.

## DEMO / 준비중

- 일일 미션 백엔드와 실제 보상
- 배틀 실시간 점수와 WebSocket
- 가챠 API, 확률, 비용
- JWT와 회원가입
- 랭킹·승급전 최종 규칙 일부
- 학습 채점 worker (`PENDING`이 유지될 수 있음)

DEMO 버튼은 실제 재화나 DB를 변경하지 않습니다. 미확정 경제·가챠·하우스 규칙도 임의로 확정하지 않습니다.
