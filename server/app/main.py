from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import CORS_ORIGINS
from app.core.exception_handlers import register_exception_handlers
from app.core.router import router as system_router
from app.battle.router import router as battle_router
from app.cats.router import router as cats_router
from app.economy.router import router as economy_router
from app.gacha.router import router as gacha_router
from app.housing.router import router as housing_router
from app.learning.router import router as learning_router
from app.ranking.router import router as ranking_router
from app.users.router import router as users_router

app = FastAPI(title="Programming Learning Cat Game API")

register_exception_handlers(app)

# Development-only browser origins used by the playable prototype.
# Keep this list narrow instead of allowing every origin.
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(system_router)
app.include_router(learning_router)
app.include_router(economy_router)
app.include_router(gacha_router)
app.include_router(cats_router)
app.include_router(housing_router)
app.include_router(ranking_router)
app.include_router(battle_router)
app.include_router(users_router)


@app.get("/")
def root():
    return {"message": "server running"}
