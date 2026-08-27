from fastapi import FastAPI

app = FastAPI(title="Programming Learning Cat Game API")


@app.get("/")
def root():
    return {"message": "server running"}
