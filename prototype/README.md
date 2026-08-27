# 플레이어블 프로토타입

현재 실행 진입점은 `prototype/index.html`이며 최신 버전은 `playable_mockup_v11.html`입니다.

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

`cat_sprite_manifest.json`으로 `cat_id`와 렌더링 asset을 연결합니다.

- 기본 / cat_id 1: 기존 주황 고양이
- cat_id 2: `assets/cats/cat_2_black_walk.webp`
- cat_id 3: `assets/cats/cat_3_white_walk.webp`

검정/흰 고양이는 각 캐릭터 컨셉 시트에서 정리한 별도 5프레임 walk strip WebP를 사용합니다.

## 멀티고양이 생활 행동 v11

`playable_mockup_v11.html`에서는 주황/검정/흰 고양이 3마리가 독립적으로 산책하면서 각자 지정된 가구 상호작용을 반복합니다.

- 주황 고양이: 소파 근처 안전 지점으로 이동한 뒤 `SIT`
- 검은 고양이: 침대 근처 안전 지점으로 이동한 뒤 `SLEEP`
- 흰 고양이: 공부 지점으로 이동한 뒤 `STUDY`
- 행동이 끝나면 다시 IDLE/랜덤 산책으로 돌아갑니다.
- 행동 목적지와 랜덤 산책을 번갈아 선택합니다.
- 이동 가능 폴리곤과 주요 가구 충돌 영역을 유지합니다.
- 직선 경로가 막히면 안전한 중간 지점을 찾아 우회합니다.
- 다른 고양이와 너무 가까우면 잠시 멈추고 다시 경로를 잡습니다.
- 각 고양이는 독립적인 위치, 상태, 프레임, 행동 타이머를 가집니다.
- 화면 라벨에서 `WALK / IDLE / SIT / SLEEP / STUDY` 상태를 바로 확인할 수 있습니다.
- 클릭하면 짧은 애정 반응 애니메이션을 합니다.

현재 `SIT/SLEEP/STUDY`는 전용 포즈 스프라이트가 아직 없으므로 같은 캐릭터 자산에 CSS 기반 작은 움직임을 더해 행동 상태를 표현합니다. 이후 전용 행동 스프라이트가 생기면 상태별 asset으로 교체할 수 있습니다.

이 동작은 플레이 감각 검증용 목업이며, 실제 서비스에서 고양이별 선호 가구나 행동 확률을 어떻게 둘지는 아직 비즈니스 규칙으로 확정하지 않습니다.

## 파일 관계

```text
index.html
└─ playable_mockup_v11.html            # 3마리 산책 + 가구 행동
   └─ playable_mockup_v9.html           # 실제 검정/흰 WebP asset 미리보기
      └─ playable_mockup_v8.html
         └─ playable_mockup_v7.html     # cat_id → sprite asset 매핑
            └─ playable_mockup_v6.html  # 실제 보유 고양이 연결
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

1. 실제 USER_CATS 수와 멀티고양이 표시를 연결
2. `SIT/SLEEP/STUDY` 전용 행동 스프라이트 추가
3. 학습 `PENDING` → Docker 채점 결과 연결
4. JWT 사용자 식별 연결
5. 가챠 정책 확정 후 실제 가챠 API 연결
