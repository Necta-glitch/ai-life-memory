from app.api.voice import router as voice_router
from app.api.memories import router as memories_router
from app.api.search import router as search_router

__all__ = ["voice_router", "memories_router", "search_router"]