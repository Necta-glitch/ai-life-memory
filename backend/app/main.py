from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.memories import router as memories_router
from app.api.search import router as search_router
from app.api.voice import router as voice_router


app = FastAPI(title="AI Life Memory API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8081", "http://localhost:19006", "http://localhost:3000", "http://localhost:8000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health_check():
    return {"status": "ok"}


app.include_router(memories_router)
app.include_router(search_router)
app.include_router(voice_router)