# 플레이어블 프로토타입

현재 실행 진입점은 `prototype/index.html`이며 최신 버전은 `playable_mockup_v12.html`입니다.

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

## 고양이 실제 스프라이트 자산

- cat_id 1: 기존 주황 고양이
- cat_id 2: `assets/cats/cat_2_black_walk.webp`
- cat_id 3: `assets/cats/cat_3_white_walk.webp`
- 그 외 cat_id: 기본 주황 스프라이트 fallback

검정/흰 고양이는 별도 5프레임 walk strip WebP를 사용합니다.

## DB 멀티고양이 하우스 v12

`playable_mockup_v12.html`부터 하우스의 멀티고양이를 3마리로 하드코딩하지 않습니다.

- 실제 `GET /users/{user_id}/cats` 결과를 사용합니다.
- USER_CATS가 0마리면 하우스에도 고양이를 만들지 않습니다.
- 보유 고양이 수만큼 캐릭터를 동적으로 생성합니다.
- 실제 `name`, `rarity`, `cat_id`, `user_cat_id`를 기준으로 표시합니다.
- cat_id 1/2/3은 주황/검정/흰 전용 외형 매핑을 사용합니다.
- 아직 전용 asset이 없는 cat_id는 기본 주황 외형으로 fallback합니다.
- 각 캐릭터는 독립 위치, `IDLE/WALK/SIT/SLEEP/STUDY`, 애니메이션 프레임, 행동 타이머를 가집니다.
- 생성된 고양이들은 산책과 가구 행동을 반복하며 다른 고양이와 너무 겹치지 않도록 이동을 조절합니다.
- SIT/SLEEP/STUDY는 아직 전용 포즈 스프라이트가 없어 CSS 기반 작은 움직임으로 표현합니다.

현재 목업은 DB가 반환한 보유 고양이를 모두 보여줍니다. 실제 서비스의 최대 하우스 배치 마릿수는 아직 비즈니스 규칙으로 확정하지 않습니다.

## 파일 관계

```text
index.html
└─ playable_mockup_v12.html            # USER_CATS 기반 동적 멀티고양이
   └─ playable_mockup_v9.html           # 실제 검정/흰 WebP asset
      └─ playable_mockup_v8.html
         └─ playable_mockup_v7.html     # cat_id → sprite asset 매핑
            └─ playable_mockup_v6.html  # 실제 보유 고양이 roster
               └─ playable_mockup_v5.html # 실제 하우징 연결
                  └─ playable_mockup_v4.html # 실제 상점 연결
                     └─ playable_mockup_v3.html # 실제 학습 연결
                        └─ playable_mockup_v2.html
                           └─ house_motion_mockup_v4.html
                              └─ house_motion_mockup_v3.html
                                 └─ house_motion_mockup_v2.html
                                    └─ house_motion_mockup.html
```

## 다음 구현 후보

1. SIT/SLEEP/STUDY 전용 행동 스프라이트 추가
2. 실제 하우스 최대 배치 마릿수/선택 규칙 확정 후 USER_CATS 배치 API 설계
3. 학습 `PENDING` → Docker 채점 결과 연결
4. JWT 사용자 식별 연결
5. 가챠 정책 확정 후 실제 가챠 API 연결
