import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.cats.models import Cat, UserCat
from app.db.database import get_db
from app.users.models import User

router = APIRouter(tags=["cats"])


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
