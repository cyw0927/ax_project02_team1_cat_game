# 플레이어블 프로토타입

현재 실행 진입점은 `prototype/index.html`이며 최신 버전은 `playable_mockup_v7.html`입니다.

## 실행

```powershell
cd server
.\.venv\Scripts\Activate.ps1
uvicorn app.main:app --reload
```

새 터미널:

```powershell
cd prototype
python -m http.server 5500
```

브라우저에서 `http://127.0.0.1:5500/`을 엽니다.

## 현재 실제 FastAPI 연결

- 학습: `GET /tasks`, `POST /attempts`
- 상점: `GET /items`, `POST /shop/buy`, `GET /users/{user_id}/inventory`
- 하우징: house 조회, 가구 배치/이동/삭제, wallpaper/floor 적용
- 보유 고양이: `GET /users/{user_id}/cats`

학습 채점 worker는 아직 연결 전이라 attempt가 `PENDING`에 머무를 수 있습니다. 데일리 퀘스트와 가챠는 아직 DEMO입니다.

## 하우스 캐릭터

현재 하우스 캐릭터는 A* 이동, 가구 충돌 회피, 자동 산책, IDLE 행동, 소파/침대/공부 상호작용, 말풍선 반응을 지원합니다.

실제 USER_CATS 목록을 roster에 표시하고 한 마리를 선택할 수 있습니다. 선택한 `user_cat_id`는 localStorage에 저장됩니다.

## 고양이 스프라이트 자산 매핑

`playable_mockup_v7.html`부터 `cat_sprite_manifest.json`을 사용합니다.

현재 manifest에는 실제로 확보된 주황 고양이 스프라이트만 기본값으로 등록되어 있습니다. 다른 DB 고양이의 외형을 이름이나 rarity만 보고 임의 생성하지 않습니다.

현재 구조:

```json
{
  "default": {
    "label": "orange-tabby-reference",
    "source": "inherited",
    "frames": 5,
    "layout": "horizontal"
  },
  "cats": {}
}
```

나중에 실제 스프라이트 파일을 `prototype/assets/cats/` 등에 추가한 뒤 `cat_id`별로 다음처럼 등록할 수 있습니다.

```json
{
  "cats": {
    "3": {
      "label": "cat-3",
      "source": "file",
      "url": "assets/cats/cat_3_walk.png",
      "frames": 5,
      "layout": "horizontal",
      "aspectRatio": "50/44"
    }
  }
}
```

선택된 DB 고양이에 전용 asset이 있으면 해당 파일로 교체하고, 없으면 default 주황 캐릭터를 그대로 사용합니다. 화면에는 현재 적용 중인 asset과 `cat_id`가 표시됩니다.

## 파일 관계

```text
index.html
└─ playable_mockup_v7.html          # cat_id → sprite asset 매핑
   └─ playable_mockup_v6.html       # 실제 보유 고양이 연결
      └─ playable_mockup_v5.html    # 실제 하우징 연결
         └─ playable_mockup_v4.html # 실제 상점 연결
            └─ playable_mockup_v3.html # 실제 학습 연결
               └─ playable_mockup_v2.html
                  └─ house_motion_mockup_v4.html
                     └─ house_motion_mockup_v3.html
                        └─ house_motion_mockup_v2.html
                           └─ house_motion_mockup.html
```

## 다음 구현 후보

1. 실제 고양이별 스프라이트 자산 추가
2. 여러 보유 고양이 동시 하우스 배치 규칙 확정 후 구현
3. 학습 `PENDING` → Docker 채점 결과 연결
4. JWT 사용자 식별 연결
5. 가챠 정책 확정 후 실제 가챠 API 연결
