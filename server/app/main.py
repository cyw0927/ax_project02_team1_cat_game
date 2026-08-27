from fastapi import FastAPI

from app.cats.router import router as cats_router
from app.economy.router import router as economy_router
from app.housing.router import router as housing_router
from app.learning.router import router as learning_router

app = FastAPI(title="Programming Learning Cat Game API")
app.include_router(learning_router)
app.include_router(economy_router)
app.include_router(cats_router)
app.include_router(housing_router)


@app.get("/")
def root():
    return {"message": "server running"}
