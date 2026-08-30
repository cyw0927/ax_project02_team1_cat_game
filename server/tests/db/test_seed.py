import json
import uuid

from app.db.seed import (
    CONCEPT_SEEDS,
    TASK_CONCEPT_IDS,
    TASK_DIFFICULTY_BASIC,
    TASK_IDS,
    TASK_TYPE_CODE,
    seed_concepts,
    seed_tasks,
)
from app.learning.models import Concept, Task


class ConceptSeedSession:
    def __init__(self) -> None:
        self.rows: dict[tuple[type, int], object] = {}

    def get(self, model, identity):
        return self.rows.get((model, identity))

    def add(self, row) -> None:
        self.rows[(type(row), row.id)] = row


def test_concept_seed_has_stable_ids_and_names():
    assert CONCEPT_SEEDS == (
        (1, "변수와 자료형"),
        (2, "조건문"),
        (3, "반복문"),
        (4, "함수"),
        (5, "리스트"),
    )


def test_concept_seed_is_idempotent():
    db = ConceptSeedSession()

    assert seed_concepts(db) == 5
    assert seed_concepts(db) == 0

    concepts = [
        row
        for (model, _), row in db.rows.items()
        if model is Concept
    ]
    assert [(concept.id, concept.name) for concept in concepts] == list(
        CONCEPT_SEEDS
    )


def test_task_seed_has_stable_ids_and_concept_references():
    assert TASK_IDS == {
        "double_number": uuid.UUID("10000000-0000-0000-0000-000000000001"),
        "is_even": uuid.UUID("10000000-0000-0000-0000-000000000002"),
        "sum_to_n": uuid.UUID("10000000-0000-0000-0000-000000000003"),
        "multiply": uuid.UUID("10000000-0000-0000-0000-000000000004"),
        "find_max": uuid.UUID("10000000-0000-0000-0000-000000000005"),
    }
    assert TASK_CONCEPT_IDS == {
        "double_number": 1,
        "is_even": 2,
        "sum_to_n": 3,
        "multiply": 4,
        "find_max": 5,
    }
    assert set(TASK_CONCEPT_IDS.values()) == {
        concept_id for concept_id, _ in CONCEPT_SEEDS
    }


def test_task_seed_is_idempotent_and_uses_valid_test_case_json():
    db = ConceptSeedSession()
    tasks = [
        Task(
            id=task_id,
            concept_id=TASK_CONCEPT_IDS[key],
            title=key,
            type=TASK_TYPE_CODE,
            difficulty=TASK_DIFFICULTY_BASIC,
            description=key,
            template_code=f"def {key}():\n    pass\n",
            test_cases=json.dumps(
                {"function_name": key, "cases": [{"args": [], "expected": 0}]}
            ),
            hint_text=None,
            is_active=True,
        )
        for key, task_id in TASK_IDS.items()
    ]

    assert seed_tasks(db, tasks) == 5
    assert seed_tasks(db, tasks) == 0

    stored_tasks = [
        row
        for (model, _), row in db.rows.items()
        if model is Task
    ]
    assert len(stored_tasks) == 5
    assert all(task.type == "CODE" for task in stored_tasks)
    assert all(task.difficulty == "BASIC" for task in stored_tasks)
    assert all(json.loads(task.test_cases)["cases"] for task in stored_tasks)
