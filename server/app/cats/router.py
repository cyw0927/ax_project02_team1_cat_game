import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.cats.models import Cat, UserCat
from app.db.database import get_db
from app.users.models import User

router = APIRouter(tags=["cats"])

STARTER_CAT_ID = 1
STARTER_CAT_NAME = "주황 고양이"
STARTER_CAT_PERSONA = "호기심 많고 다정한 첫 친구"
STARTER_CAT_RARITY = "STARTER"


def ensure_starter_cat(user_id: uuid.UUID, db: Session) -> UserCat:
    """Ensure that a user owns the starter orange cat exactly once in normal flow.

    This helper is intentionally reusable so the future signup/login flow can call the
    same provisioning logic instead of duplicating starter-reward rules.
    """
    if db.get(User, user_id) is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    existing = db.scalar(
        select(UserCat)
        .where(
            UserCat.user_id == user_id,
            UserCat.cat_id == STARTER_CAT_ID,
        )
        .limit(1)
    )
    if existing is not None:
        return existing

    starter = db.get(Cat, STARTER_CAT_ID)
    if starter is None:
        starter = Cat(
            id=STARTER_CAT_ID,
            name=STARTER_CAT_NAME,
            persona=STARTER_CAT_PERSONA,
            rarity=STARTER_CAT_RARITY,
        )
        db.add(starter)
        db.flush()

    user_cat = UserCat(user_id=user_id, cat_id=STARTER_CAT_ID)
    db.add(user_cat)
    db.commit()
    db.refresh(user_cat)
    return user_cat


@router.get("/cats")
def get_cats(db: Session = Depends(get_db)):
    cats = db.scalars(select(Cat).order_by(Cat.id)).all()

    return [
        {
            "id": cat.id,
            "name": cat.name,
            "persona": cat.persona,
            "rarity": cat.rarity,
        }
        for cat in cats
    ]


@router.post("/users/{user_id}/cats/starter")
def provision_starter_cat(
    user_id: uuid.UUID,
    db: Session = Depends(get_db),
):
    user_cat = ensure_starter_cat(user_id, db)
    cat = db.get(Cat, user_cat.cat_id)

    return {
        "user_cat_id": user_cat.id,
        "cat_id": cat.id,
        "name": cat.name,
        "persona": cat.persona,
        "rarity": cat.rarity,
    }


@router.get("/users/{user_id}/cats")
def get_user_cats(user_id: uuid.UUID, db: Session = Depends(get_db)):
    if db.get(User, user_id) is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    rows = db.execute(
        select(
            UserCat.id,
            Cat.id,
            Cat.name,
            Cat.persona,
            Cat.rarity,
        )
        .join(Cat, Cat.id == UserCat.cat_id)
        .where(UserCat.user_id == user_id)
        .order_by(UserCat.id)
    ).all()

    return [
        {
            "user_cat_id": user_cat_id,
            "cat_id": cat_id,
            "name": name,
            "persona": persona,
            "rarity": rarity,
        }
        for user_cat_id, cat_id, name, persona, rarity in rows
    ]
