import uuid

from sqlalchemy import select

from app.cats.models import Cat
from app.db.database import SessionLocal
from app.economy.models import Item
from app.learning.models import Concept
from app.users.models import User


DEV_USER_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")


def seed_master_data() -> None:
    db = SessionLocal()
    created_count = 0

    try:
        concepts = [
            Concept(id=1, name="변수와 자료형"),
            Concept(id=2, name="조건문"),
            Concept(id=3, name="반복문"),
            Concept(id=4, name="함수"),
            Concept(id=5, name="리스트"),
        ]

        for concept in concepts:
            if db.get(Concept, concept.id) is None:
                db.add(concept)
                created_count += 1

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