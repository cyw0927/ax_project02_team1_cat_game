# 플레이어블 프로토타입

현재 실행 진입점은 `prototype/index.html`이며 최신 버전은 `playable_mockup_v13.html`입니다.

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
- 스타터 고양이: `POST /users/{user_id}/cats/starter`

학습 채점 worker는 아직 연결 전이라 attempt가 `PENDING`에 머무를 수 있습니다. 데일리 퀘스트와 가챠는 아직 DEMO입니다.

## 스타터 주황 고양이 v13

게임 시작 시 고양이가 한 마리도 없어 플레이가 막히지 않도록 주황 고양이를 기본 스타터로 보장합니다.

- 기본 스타터는 `cat_id=1` 주황 고양이입니다.
- `POST /users/{user_id}/cats/starter`가 스타터 보유 여부를 확인합니다.
- 이미 `cat_id=1`을 보유한 사용자는 중복 지급하지 않습니다.
- 스타터 Cat 마스터가 아직 DB에 없으면 기본 이름/페르소나/rarity로 생성한 뒤 지급합니다.
- 현재 회원가입 API가 아직 없으므로 `playable_mockup_v13.html`이 USER_CATS 조회 전에 이 API를 자동 호출합니다.
- 추후 Auth/회원가입 구현 시 같은 starter provisioning 로직을 신규 사용자 생성 트랜잭션에서 호출하도록 이동할 수 있습니다.

## 고양이 실제 스프라이트 자산

- cat_id 1: 기존 주황 고양이
- cat_id 2: `assets/cats/cat_2_black_walk.webp`
- cat_id 3: `assets/cats/cat_3_white_walk.webp`
- 그 외 cat_id: 기본 주황 스프라이트 fallback

검정/흰 고양이는 별도 5프레임 walk strip WebP를 사용합니다.

## DB 멀티고양이 하우스

`playable_mockup_v12.html`의 USER_CATS 기반 동적 생성 로직을 v13이 그대로 사용합니다.

- 실제 `GET /users/{user_id}/cats` 결과 사용
- 보유 고양이 수만큼 캐릭터 동적 생성
- 실제 `name`, `rarity`, `cat_id`, `user_cat_id` 표시
- 각 캐릭터 독립 `IDLE/WALK/SIT/SLEEP/STUDY`
- 랜덤 산책, 가구 충돌 회피, 고양이 간 최소 거리 조절
- SIT/SLEEP/STUDY는 현재 CSS 기반 행동 표현

## 파일 관계

```text
index.html
└─ playable_mockup_v13.html            # 스타터 주황 고양이 자동 보장
   └─ playable_mockup_v12.html          # USER_CATS 기반 동적 멀티고양이
      └─ playable_mockup_v9.html        # 실제 검정/흰 WebP asset
         └─ playable_mockup_v8.html
            └─ playable_mockup_v7.html  # cat_id → sprite asset 매핑
               └─ playable_mockup_v6.html
                  └─ playable_mockup_v5.html
                     └─ playable_mockup_v4.html
                        └─ playable_mockup_v3.html
                           └─ playable_mockup_v2.html
                              └─ house_motion_mockup_v4.html
                                 └─ house_motion_mockup_v3.html
                                    └─ house_motion_mockup_v2.html
                                       └─ house_motion_mockup.html
```

## 다음 구현 후보

1. SIT/SLEEP/STUDY 전용 행동 스프라이트 추가
2. 학습 `PENDING` → Docker 채점 결과 연결
3. JWT 사용자 식별과 실제 회원가입 시 starter 지급 연결
4. 실제 하우스 최대 배치 마릿수/선택 규칙 확정
5. 가챠 정책 확정 후 실제 가챠 API 연결
