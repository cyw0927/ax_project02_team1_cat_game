# 플레이어블 프로토타입

현재 실행 진입점은 `prototype/index.html`이며 최신 버전은 `playable_mockup_v9.html`입니다.

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

## 고양이 실제 스프라이트 자산

`cat_sprite_manifest.json`으로 `cat_id`와 렌더링 asset을 연결합니다.

현재 프로토타입 매핑:

- 기본 / cat_id 1 미리보기: 기존 주황 고양이
- cat_id 2: `assets/cats/cat_2_black_walk.webp`
- cat_id 3: `assets/cats/cat_3_white_walk.webp`

검정/흰 고양이는 더 이상 색상 필터로 만든 외형이 아니라, 각 캐릭터 컨셉 시트에서 정리한 별도 5프레임 walk strip WebP를 사용합니다. 현재 파일은 빠른 목업 검증을 위해 용량을 줄인 프로토타입 자산이며 최종 아트 단계에서 더 높은 해상도의 투명 자산으로 교체할 수 있습니다.

`playable_mockup_v9.html`에서는 House 화면 아래 `주황 / 검정 / 흰색` 버튼으로 실제 asset 교체를 DB와 별개로 즉시 확인할 수 있습니다. 실제 DB 고양이를 선택하는 v7 매핑도 같은 manifest를 사용합니다.

## 파일 관계

```text
index.html
└─ playable_mockup_v9.html             # 실제 검정/흰 WebP asset 미리보기
   └─ playable_mockup_v8.html          # 이전 외형 미리보기
      └─ playable_mockup_v7.html       # cat_id → sprite asset 매핑
         └─ playable_mockup_v6.html    # 실제 보유 고양이 연결
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

1. 여러 보유 고양이를 하우스에 동시에 보여주는 목업
2. 학습 `PENDING` → Docker 채점 결과 연결
3. JWT 사용자 식별 연결
4. 가챠 정책 확정 후 실제 가챠 API 연결
5. 최종 고해상도 캐릭터/가구 아트 자산 교체
