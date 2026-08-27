# Alembic Migration Guide

이 디렉터리는 PostgreSQL 데이터베이스 스키마 변경 이력을 관리합니다.

## 1. 환경 준비

`server/.env` 파일에 PostgreSQL 연결 정보를 설정합니다.

```env
DATABASE_URL=postgresql+psycopg://postgres:your_password@localhost:5432/cat_game
```

필요한 패키지를 설치합니다.

```powershell
pip install -r requirements.txt
```

## 2. 첫 마이그레이션 생성

`server` 디렉터리에서 실행합니다.

```powershell
alembic revision --autogenerate -m "initial schema"
```

생성된 파일은 `alembic/versions/` 아래에 저장됩니다.

자동 생성된 마이그레이션은 실행하기 전에 반드시 내용을 확인합니다.

## 3. 마이그레이션 적용

```powershell
alembic upgrade head
```

## 4. 현재 적용 상태 확인

```powershell
alembic current
```

## 5. 마이그레이션 이력 확인

```powershell
alembic history
```

## 주의사항

- 실제 비밀번호가 들어간 `.env` 파일은 Git에 커밋하지 않습니다.
- 테이블 구조 변경 후에는 새로운 migration을 생성합니다.
- 팀원이 이미 사용 중인 migration 파일은 임의로 수정하지 말고 새 migration을 추가하는 방식으로 관리합니다.
- `Base.metadata.create_all()`은 초기 확인용으로만 사용하고, 이후 스키마 변경은 Alembic으로 관리합니다.
