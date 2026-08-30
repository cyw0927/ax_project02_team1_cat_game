import json
import uuid

from sqlalchemy import select

from app.cats.models import Cat
from app.db.database import SessionLocal
from app.economy.models import Item
from app.learning.models import Concept, Task
from app.users.models import User


DEV_USER_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")
CONCEPT_SEEDS = (
    (1, "변수와 자료형"),
    (2, "조건문"),
    (3, "반복문"),
    (4, "함수"),
    (5, "리스트"),
)
TASK_IDS = {
    "double_number": uuid.UUID(
        "10000000-0000-0000-0000-000000000001"
    ),
    "is_even": uuid.UUID(
        "10000000-0000-0000-0000-000000000002"
    ),
    "sum_to_n": uuid.UUID(
        "10000000-0000-0000-0000-000000000003"
    ),
    "multiply": uuid.UUID(
        "10000000-0000-0000-0000-000000000004"
    ),
    "find_max": uuid.UUID(
        "10000000-0000-0000-0000-000000000005"
    ),
}
TASK_CONCEPT_IDS = {
    "double_number": 1,
    "is_even": 2,
    "sum_to_n": 3,
    "multiply": 4,
    "find_max": 5,
}
TASK_TYPE_CODE = "CODE"
TASK_DIFFICULTY_BASIC = "BASIC"


def seed_concepts(db) -> int:
    """고정 ID의 기본 학습 개념을 멱등하게 생성한다."""

    created_count = 0

    for concept_id, name in CONCEPT_SEEDS:
        if db.get(Concept, concept_id) is None:
            db.add(Concept(id=concept_id, name=name))
            created_count += 1

    return created_count


def seed_tasks(db, tasks: list[Task]) -> int:
    """고정 UUID의 기본 문제를 멱등하게 생성한다."""

    created_count = 0

    for task in tasks:
        if db.get(Task, task.id) is None:
            db.add(task)
            created_count += 1

    return created_count


def seed_master_data() -> None:
    db = SessionLocal()
    created_count = 0

    try:
        created_count += seed_concepts(db)

        tasks = [
            Task(
                id=TASK_IDS["double_number"],
                concept_id=TASK_CONCEPT_IDS["double_number"],
                title="숫자를 두 배로 만들기",
                type=TASK_TYPE_CODE,
                difficulty=TASK_DIFFICULTY_BASIC,
                description=(
                    "숫자 하나를 받아 두 배로 반환하는 "
                    "double_number 함수를 작성하세요."
                ),
                template_code=(
                    "def double_number(number):\n"
                    "    # 코드를 작성하세요.\n"
                    "    pass\n"
                ),
                test_cases=json.dumps(
                    {
                        "function_name": "double_number",
                        "cases": [
                            {"args": [3], "expected": 6},
                            {"args": [0], "expected": 0},
                            {"args": [-4], "expected": -8},
                        ],
                    },
                    ensure_ascii=False,
                ),
                hint_text="입력받은 number에 2를 곱해 보세요.",
                is_active=True,
            ),
            Task(
                id=TASK_IDS["is_even"],
                concept_id=TASK_CONCEPT_IDS["is_even"],
                title="짝수 판별하기",
                type=TASK_TYPE_CODE,
                difficulty=TASK_DIFFICULTY_BASIC,
                description=(
                    "정수를 받아 짝수이면 True, 홀수이면 False를 "
                    "반환하는 is_even 함수를 작성하세요."
                ),
                template_code=(
                    "def is_even(number):\n"
                    "    # 코드를 작성하세요.\n"
                    "    pass\n"
                ),
                test_cases=json.dumps(
                    {
                        "function_name": "is_even",
                        "cases": [
                            {"args": [2], "expected": True},
                            {"args": [7], "expected": False},
                            {"args": [0], "expected": True},
                        ],
                    },
                    ensure_ascii=False,
                ),
                hint_text="2로 나눈 나머지가 0인지 확인하세요.",
                is_active=True,
            ),
            Task(
                id=TASK_IDS["sum_to_n"],
                concept_id=TASK_CONCEPT_IDS["sum_to_n"],
                title="1부터 N까지 더하기",
                type=TASK_TYPE_CODE,
                difficulty=TASK_DIFFICULTY_BASIC,
                description=(
                    "양의 정수 n을 받아 1부터 n까지의 합을 반환하는 "
                    "sum_to_n 함수를 반복문으로 작성하세요."
                ),
                template_code=(
                    "def sum_to_n(n):\n"
                    "    # 코드를 작성하세요.\n"
                    "    pass\n"
                ),
                test_cases=json.dumps(
                    {
                        "function_name": "sum_to_n",
                        "cases": [
                            {"args": [1], "expected": 1},
                            {"args": [5], "expected": 15},
                            {"args": [10], "expected": 55},
                        ],
                    },
                    ensure_ascii=False,
                ),
                hint_text="합계를 저장할 변수를 만들고 반복해서 더하세요.",
                is_active=True,
            ),
            Task(
                id=TASK_IDS["multiply"],
                concept_id=TASK_CONCEPT_IDS["multiply"],
                title="두 수를 곱하는 함수",
                type=TASK_TYPE_CODE,
                difficulty=TASK_DIFFICULTY_BASIC,
                description=(
                    "두 수 a와 b를 받아 곱한 값을 반환하는 "
                    "multiply 함수를 작성하세요."
                ),
                template_code=(
                    "def multiply(a, b):\n"
                    "    # 코드를 작성하세요.\n"
                    "    pass\n"
                ),
                test_cases=json.dumps(
                    {
                        "function_name": "multiply",
                        "cases": [
                            {"args": [2, 3], "expected": 6},
                            {"args": [0, 10], "expected": 0},
                            {"args": [-2, 4], "expected": -8},
                        ],
                    },
                    ensure_ascii=False,
                ),
                hint_text="함수의 두 매개변수 a와 b를 곱해 반환하세요.",
                is_active=True,
            ),
            Task(
                id=TASK_IDS["find_max"],
                concept_id=TASK_CONCEPT_IDS["find_max"],
                title="리스트에서 최댓값 찾기",
                type=TASK_TYPE_CODE,
                difficulty=TASK_DIFFICULTY_BASIC,
                description=(
                    "숫자 리스트를 받아 가장 큰 값을 반환하는 "
                    "find_max 함수를 작성하세요."
                ),
                template_code=(
                    "def find_max(numbers):\n"
                    "    # 코드를 작성하세요.\n"
                    "    pass\n"
                ),
                test_cases=json.dumps(
                    {
                        "function_name": "find_max",
                        "cases": [
                            {
                                "args": [[1, 3, 2]],
                                "expected": 3,
                            },
                            {
                                "args": [[-5, -2, -9]],
                                "expected": -2,
                            },
                            {
                                "args": [[7]],
                                "expected": 7,
                            },
                        ],
                    },
                    ensure_ascii=False,
                ),
                hint_text=(
                    "첫 번째 값을 기준으로 잡고 나머지 값과 "
                    "차례대로 비교해 보세요."
                ),
                is_active=True,
            ),
        ]

        created_count += seed_tasks(db, tasks)

        items = [
            Item(
                id=1,
                category="WALLPAPER",
                name="파란 별 벽지",
                price=500,
            ),
            Item(
                id=2,
                category="FLOOR",
                name="원목 바닥",
                price=400,
            ),
            Item(
                id=3,
                category="FURNITURE",
                name="기본 캣타워",
                price=800,
            ),
            Item(
                id=4,
                category="FURNITURE",
                name="학습용 책상",
                price=600,
            ),
        ]

        for item in items:
            if db.get(Item, item.id) is None:
                db.add(item)
                created_count += 1

        cats = [
            Cat(
                id=1,
                name="나비",
                persona="밝고 호기심이 많은 고양이",
                rarity="N",
            ),
            Cat(
                id=2,
                name="구름",
                persona="느긋하고 다정한 고양이",
                rarity="R",
            ),
            Cat(
                id=3,
                name="별이",
                persona="활발하고 장난기가 많은 고양이",
                rarity="SR",
            ),
            Cat(
                id=4,
                name="루나",
                persona="차분하고 따뜻하게 응원해 주는 고양이",
                rarity="SSR",
            ),
        ]

        for cat in cats:
            if db.get(Cat, cat.id) is None:
                db.add(cat)
                created_count += 1

        dev_user_exists = db.scalar(
            select(User.id).where(
                User.external_student_id == "DEV-001"
            )
        )

        if dev_user_exists is None:
            db.add(
                User(
                    id=DEV_USER_ID,
                    external_student_id="DEV-001",
                    username="개발용 학습자",
                    role="USER",
                    soft_balance=1000,
                    hard_balance=100,
                    mileage=0,
                    house_level=1,
                    wallpaper_item_id=None,
                    floor_item_id=None,
                )
            )
            created_count += 1

        db.commit()
        print(f"Seed completed: {created_count} row(s) created.")

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


if __name__ == "__main__":
    seed_master_data()
