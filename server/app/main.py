from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.battle.router import router as battle_router
from app.cats.router import router as cats_router
from app.economy.router import router as economy_router
from app.housing.router import router as housing_router
from app.learning.router import router as learning_router
from app.ranking.router import router as ranking_router
from app.users.router import router as users_router

app = FastAPI(title="Programming Learning Cat Game API")

# Development-only browser origins used by the playable prototype.
# Keep this list narrow instead of allowing every origin.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5500",
        "http://127.0.0.1:5500",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
