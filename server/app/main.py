from fastapi import FastAPI

from app.economy.router import router as economy_router
from app.learning.router import router as learning_router

app = FastAPI(title="Programming Learning Cat Game API")
app.include_router(learning_router)
app.include_router(economy_router)


@app.get("/")
def root():
    return {"message": "server running"}
