# Local Setup

## Repository 위치 확인

`git pull`은 반드시 `.git`이 존재하는 실제 저장소 폴더 안에서 실행해야 합니다.

예시:

```powershell
cd C:\dev\ax_project02_team1_cat_game-main\ax_project02_team1_cat_game
git status
git pull
```

부모 폴더에서 실행하면 다음 오류가 발생합니다.

```text
fatal: not a git repository (or any of the parent directories): .git
```

## FastAPI 실행

```powershell
cd server
.\.venv\Scripts\Activate.ps1
uvicorn app.main:app --reload
```

## Prototype 실행

새 터미널에서:

```powershell
cd prototype
python -m http.server 5500
```

브라우저:

```text
http://127.0.0.1:5500/
```

프로젝트 구조나 실행 방법이 바뀌면 이 문서를 함께 갱신합니다.
