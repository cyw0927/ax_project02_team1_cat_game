import asyncio
import uuid
from datetime import UTC, datetime

import httpx

from app.db.database import get_db
from app.learning.models import Concept, Task
from app.main import app
from app.users.models import User


def build_user(role: str = "USER") -> User:
    return User(
        id=uuid.uuid4(),
        external_student_id=f"TEST-{uuid.uuid4()}",
        username="개념 테스트 사용자",
        role=role,
        soft_balance=0,
        hard_balance=0,
        mileage=0,
        house_level=1,
        wallpaper_item_id=None,
        floor_item_id=None,
        created_at=datetime.now(UTC),
    )


class ConceptSession:
    def __init__(
        self,
        user: User,
        concepts: list[Concept] | None = None,
    ) -> None:
        self.user = user
        self.concepts = concepts or []
        self.statement = None

    def get(self, model, identity):
        if model is User and identity == self.user.id:
            return self.user
        return None

    def scalars(self, statement):
        self.statement = statement

        class Result:
            def __init__(self, values):
                self.values = values

            def all(self):
                return self.values

        return Result(self.concepts)


def get_concepts_response(
    db: ConceptSession,
    header_value: str | None,
) -> httpx.Response:
    def override_get_db():
        yield db

    async def request() -> httpx.Response:
        transport = httpx.ASGITransport(app=app)
        headers = {}
        if header_value is not None:
            headers["X-User-ID"] = header_value

        async with httpx.AsyncClient(
            transport=transport,
            base_url="http://testserver",
        ) as client:
            return await client.get("/concepts", headers=headers)

    app.dependency_overrides[get_db] = override_get_db
    try:
        return asyncio.run(request())
    finally:
        app.dependency_overrides.clear()


def test_get_concepts_returns_ordered_response_contract():
    user = build_user()
    db = ConceptSession(
        user,
        [
            Concept(id=1, name="변수와 자료형"),
            Concept(id=2, name="조건문"),
        ],
    )

    response = get_concepts_response(db, str(user.id))

    assert response.status_code == 200
    assert response.json() == [
        {"id": 1, "name": "변수와 자료형"},
        {"id": 2, "name": "조건문"},
    ]
    assert "ORDER BY concepts.id" in str(db.statement)


def test_get_concepts_returns_empty_list():
    user = build_user()
    db = ConceptSession(user)

    response = get_concepts_response(db, str(user.id))

    assert response.status_code == 200
    assert response.json() == []


def test_get_concepts_requires_current_user():
    user = build_user()
    db = ConceptSession(user)

    response = get_concepts_response(db, None)

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "CURRENT_USER_ID_REQUIRED"


def test_get_concepts_rejects_unsupported_role():
    user = build_user(role="GUEST")
    db = ConceptSession(user)

    response = get_concepts_response(db, str(user.id))

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "INSUFFICIENT_ROLE"


class ConceptTaskSession:
    def __init__(
        self,
        user: User,
        concept: Concept | None,
        tasks: list[Task] | None = None,
    ) -> None:
        self.user = user
        self.concept = concept
        self.tasks = tasks or []
        self.statement = None

    def get(self, model, identity):
        if model is User and identity == self.user.id:
            return self.user
        if model is Concept and self.concept is not None:
            if identity == self.concept.id:
                return self.concept
        return None

    def scalars(self, statement):
        self.statement = statement

        class Result:
            def __init__(self, values):
                self.values = values

            def all(self):
                return self.values

        return Result(self.tasks)


def get_concept_tasks_response(
    db: ConceptTaskSession,
    concept_id: int,
) -> httpx.Response:
    def override_get_db():
        yield db

    async def request() -> httpx.Response:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(
            transport=transport,
            base_url="http://testserver",
        ) as client:
            return await client.get(
                f"/concepts/{concept_id}/tasks",
                headers={"X-User-ID": str(db.user.id)},
            )

    app.dependency_overrides[get_db] = override_get_db
    try:
        return asyncio.run(request())
    finally:
        app.dependency_overrides.clear()


def build_task(concept_id: int) -> Task:
    return Task(
        id=uuid.uuid4(),
        concept_id=concept_id,
        title="테스트 문제",
        type="CODE",
        difficulty="BASIC",
        description="목록에서 제외할 설명",
        template_code="목록에서 제외할 코드",
        test_cases='{"secret": true}',
        hint_text="목록에서 제외할 힌트",
        is_active=True,
    )


def test_get_concept_tasks_returns_only_public_summary_fields():
    user = build_user()
    concept = Concept(id=1, name="변수와 자료형")
    task = build_task(concept.id)
    db = ConceptTaskSession(user, concept, [task])

    response = get_concept_tasks_response(db, concept.id)

    assert response.status_code == 200
    assert response.json() == [
        {
            "id": str(task.id),
            "concept_id": concept.id,
            "title": "테스트 문제",
            "type": "CODE",
            "difficulty": "BASIC",
            "is_locked": False,
        }
    ]
    statement = str(db.statement)
    assert "tasks.concept_id" in statement
    assert "tasks.is_active IS true" in statement
    assert "ORDER BY tasks.id" in statement


def test_get_concept_tasks_returns_empty_list_for_concept_without_tasks():
    user = build_user()
    concept = Concept(id=1, name="변수와 자료형")
    db = ConceptTaskSession(user, concept)

    response = get_concept_tasks_response(db, concept.id)

    assert response.status_code == 200
    assert response.json() == []


def test_get_concept_tasks_returns_404_for_unknown_concept():
    user = build_user()
    db = ConceptTaskSession(user, concept=None)

    response = get_concept_tasks_response(db, concept_id=999)

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "CONCEPT_NOT_FOUND"
    assert db.statement is None


class TaskDetailSession:
    def __init__(self, user: User, task: Task | None) -> None:
        self.user = user
        self.task = task
        self.statement = None

    def get(self, model, identity):
        if model is User and identity == self.user.id:
            return self.user
        return None

    def scalar(self, statement):
        self.statement = statement
        return self.task


def get_task_detail_response(
    db: TaskDetailSession,
    task_id: uuid.UUID,
) -> httpx.Response:
    def override_get_db():
        yield db

    async def request() -> httpx.Response:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(
            transport=transport,
            base_url="http://testserver",
        ) as client:
            return await client.get(
                f"/tasks/{task_id}",
                headers={"X-User-ID": str(db.user.id)},
            )

    app.dependency_overrides[get_db] = override_get_db
    try:
        return asyncio.run(request())
    finally:
        app.dependency_overrides.clear()


def test_get_task_detail_returns_description_and_template_without_secrets():
    user = build_user()
    task = build_task(concept_id=1)
    db = TaskDetailSession(user, task)

    response = get_task_detail_response(db, task.id)

    assert response.status_code == 200
    assert response.json() == {
        "id": str(task.id),
        "concept_id": 1,
        "title": "테스트 문제",
        "type": "CODE",
        "difficulty": "BASIC",
        "is_locked": False,
        "description": "목록에서 제외할 설명",
        "template_code": "목록에서 제외할 코드",
    }
    statement = str(db.statement)
    assert "tasks.id" in statement
    assert "tasks.is_active IS true" in statement


def test_get_task_detail_returns_404_for_missing_or_inactive_task():
    user = build_user()
    db = TaskDetailSession(user, task=None)

    response = get_task_detail_response(db, uuid.uuid4())

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "TASK_NOT_FOUND"


def get_task_catalog_response(db: ConceptTaskSession) -> httpx.Response:
    def override_get_db():
        yield db

    async def request() -> httpx.Response:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(
            transport=transport,
            base_url="http://testserver",
        ) as client:
            return await client.get(
                "/tasks",
                headers={"X-User-ID": str(db.user.id)},
            )

    app.dependency_overrides[get_db] = override_get_db
    try:
        return asyncio.run(request())
    finally:
        app.dependency_overrides.clear()


def test_legacy_task_catalog_is_authenticated_active_only_and_deprecated():
    user = build_user()
    task = build_task(concept_id=1)
    db = ConceptTaskSession(user, concept=None, tasks=[task])

    response = get_task_catalog_response(db)

    assert response.status_code == 200
    assert response.json() == [
        {
            "id": str(task.id),
            "concept_id": 1,
            "title": "테스트 문제",
            "type": "CODE",
            "difficulty": "BASIC",
            "is_locked": False,
            "template_code": "목록에서 제외할 코드",
        }
    ]
    statement = str(db.statement)
    assert "tasks.is_active IS true" in statement
    assert "ORDER BY tasks.id" in statement
    assert app.openapi()["paths"]["/tasks"]["get"]["deprecated"] is True


def use_task_hint_response(
    db: TaskDetailSession,
    task_id: uuid.UUID,
) -> httpx.Response:
    def override_get_db():
        yield db

    async def request() -> httpx.Response:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(
            transport=transport,
            base_url="http://testserver",
        ) as client:
            return await client.post(
                f"/tasks/{task_id}/hint",
                headers={"X-User-ID": str(db.user.id)},
            )

    app.dependency_overrides[get_db] = override_get_db
    try:
        return asyncio.run(request())
    finally:
        app.dependency_overrides.clear()


def test_use_task_hint_returns_hint_and_usage_flag():
    user = build_user()
    task = build_task(concept_id=1)
    db = TaskDetailSession(user, task)

    response = use_task_hint_response(db, task.id)

    assert response.status_code == 200
    assert response.json() == {
        "task_id": str(task.id),
        "hint_text": "목록에서 제외할 힌트",
        "used_hint": True,
    }
    assert "tasks.is_active IS true" in str(db.statement)


def test_use_task_hint_returns_404_when_hint_is_not_available():
    user = build_user()
    task = build_task(concept_id=1)
    task.hint_text = None
    db = TaskDetailSession(user, task)

    response = use_task_hint_response(db, task.id)

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "HINT_NOT_AVAILABLE"


def test_use_task_hint_returns_404_for_missing_or_inactive_task():
    user = build_user()
    db = TaskDetailSession(user, task=None)

    response = use_task_hint_response(db, uuid.uuid4())

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "TASK_NOT_FOUND"


def test_task_response_schemas_never_expose_test_cases():
    schemas = app.openapi()["components"]["schemas"]

    for schema_name in (
        "TaskSummaryResponse",
        "TaskDetailResponse",
        "TaskCatalogResponse",
        "TaskHintResponse",
    ):
        properties = schemas[schema_name]["properties"]
        assert "test_cases" not in properties


def test_public_task_routes_do_not_declare_test_cases_in_responses():
    openapi_paths = app.openapi()["paths"]

    for path, method in (
        ("/concepts/{concept_id}/tasks", "get"),
        ("/tasks/{task_id}", "get"),
        ("/tasks", "get"),
        ("/tasks/{task_id}/hint", "post"),
    ):
        response_contract = str(openapi_paths[path][method]["responses"])
        assert "test_cases" not in response_contract
