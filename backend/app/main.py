from fastapi import FastAPI

from app.api.memories import router as memories_router


app = FastAPI(title="AI Life Memory API")


@app.get("/health")
def health_check():
    return {"status": "ok"}


app.include_router(memories_router)