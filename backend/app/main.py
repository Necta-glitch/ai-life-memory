from fastapi import FastAPI

from app.api.memories import router as memories_router
from app.api.search import router as search_router
from app.api.voice import router as voice_router


app = FastAPI(title="AI Life Memory API")


@app.get("/health")
def health_check():
    return {"status": "ok"}


app.include_router(memories_router)
app.include_router(search_router)
app.include_router(voice_router)