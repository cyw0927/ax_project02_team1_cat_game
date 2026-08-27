from fastapi import FastAPI

from app.battle.router import router as battle_router
from app.cats.router import router as cats_router
from app.economy.router import router as economy_router
from app.housing.router import router as housing_router
from app.learning.router import router as learning_router
from app.ranking.router import router as ranking_router
from app.users.router import router as users_router

app = FastAPI(title="Programming Learning Cat Game API")
app.include_router(learning_router)
app.include_router(economy_router)
app.include_router(cats_router)
app.include_router(housing_router)
app.include_router(ranking_router)
app.include_router(battle_router)
app.include_router(users_router)


@app.get("/")
def root():
    return {"message": "server running"}
