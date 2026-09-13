import pytest
import pytest_asyncio
from unittest.mock import Mock, MagicMock
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.db.database import get_db
from app.main import app
from app.ai.schemas import AIProcessingResult
from app.ai.service import AIService


SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db_session():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def mock_ai_service():
    """Mock AIService for testing."""
    mock_service = Mock(spec=AIService)
    mock_service.process_memory.return_value = AIProcessingResult(
        summary="Test summary",
        topics=["test", "topic"],
        entities=["test", "entity"],
    )
    return mock_service


@pytest_asyncio.fixture(scope="function")
async def client(db_session, mock_ai_service):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    # Override MemoryService's AIService with mock
    from app.api.memories import memory_service
    memory_service.ai_service = mock_ai_service

    app.dependency_overrides[get_db] = override_get_db
    from httpx import ASGITransport, AsyncClient

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c
    app.dependency_overrides.clear()