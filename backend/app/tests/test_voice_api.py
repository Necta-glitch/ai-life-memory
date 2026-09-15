"""Tests for voice memory API endpoints."""

from datetime import datetime
from unittest.mock import AsyncMock, Mock

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.exc import SQLAlchemyError

from app.ai.transcription_service import TranscriptionError
from app.main import app
from app.api.voice import (
    get_memory_service,
    get_transcription_service,
)
from app.schemas.memory import MemoryResponse


client = TestClient(app)


@pytest.fixture
def mock_transcription_service():
    """Create a mocked transcription service."""
    service = Mock()
    service.transcribe = AsyncMock(return_value="This is a test voice memory.")
    return service


@pytest.fixture
def mock_memory_service():
    """Create a mocked memory service."""
    service = Mock()

    service.create_memory = Mock(
        return_value=MemoryResponse(
            id=1,
            user_id="dev-user",
            content="This is a test voice memory.",
            source="voice",
            summary=None,
            topics=[],
            embedding=None,
            created_at=datetime(2026, 9, 14, 12, 0, 0),
            occurred_at=None,
        )
    )

    return service


@pytest.fixture(autouse=True)
def clear_dependency_overrides():
    """Clear FastAPI dependency overrides before and after each test."""
    app.dependency_overrides.clear()

    yield

    app.dependency_overrides.clear()


def override_services(mock_transcription_service, mock_memory_service):
    """Override voice endpoint dependencies."""
    app.dependency_overrides[get_transcription_service] = (
        lambda: mock_transcription_service
    )

    app.dependency_overrides[get_memory_service] = (
        lambda: mock_memory_service
    )


def test_create_voice_memory_success(
    mock_transcription_service,
    mock_memory_service,
):
    """Test successful voice memory creation."""

    override_services(
        mock_transcription_service,
        mock_memory_service,
    )

    response = client.post(
        "/memories/voice",
        files={
            "audio": (
                "test.mp3",
                b"fake audio content",
                "audio/mpeg",
            )
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["id"] == 1
    assert data["user_id"] == "dev-user"
    assert data["content"] == "This is a test voice memory."
    assert data["source"] == "voice"

    mock_transcription_service.transcribe.assert_awaited_once()
    mock_memory_service.create_memory.assert_called_once()


def test_create_voice_memory_user_isolation(
    mock_transcription_service,
    mock_memory_service,
):
    """Test that the user ID is passed correctly to the memory service."""

    override_services(
        mock_transcription_service,
        mock_memory_service,
    )

    response = client.post(
        "/memories/voice?user_id=user-123",
        files={
            "audio": (
                "test.mp3",
                b"fake audio content",
                "audio/mpeg",
            )
        },
    )

    assert response.status_code == 201

    mock_memory_service.create_memory.assert_called_once()

    call_kwargs = mock_memory_service.create_memory.call_args.kwargs

    assert call_kwargs["user_id"] == "user-123"


def test_create_voice_memory_header_user_id(
    mock_transcription_service,
    mock_memory_service,
):
    """Test that X-User-ID header takes precedence."""

    override_services(
        mock_transcription_service,
        mock_memory_service,
    )

    response = client.post(
        "/memories/voice?user_id=query-user",
        headers={
            "X-User-ID": "header-user",
        },
        files={
            "audio": (
                "test.mp3",
                b"fake audio content",
                "audio/mpeg",
            )
        },
    )

    assert response.status_code == 201

    mock_memory_service.create_memory.assert_called_once()

    call_kwargs = mock_memory_service.create_memory.call_args.kwargs

    assert call_kwargs["user_id"] == "header-user"


def test_create_voice_memory_occurred_at(
    mock_transcription_service,
    mock_memory_service,
):
    """Test that occurred_at is passed correctly."""

    override_services(
        mock_transcription_service,
        mock_memory_service,
    )

    occurred_at = "2026-09-10T15:30:00"

    response = client.post(
        "/memories/voice",
        data={
            "occurred_at": occurred_at,
        },
        files={
            "audio": (
                "test.mp3",
                b"fake audio content",
                "audio/mpeg",
            )
        },
    )

    assert response.status_code == 201

    mock_memory_service.create_memory.assert_called_once()

    call_kwargs = mock_memory_service.create_memory.call_args.kwargs

    memory_create = call_kwargs["memory"]

    assert memory_create.occurred_at == datetime.fromisoformat(occurred_at)


def test_create_voice_memory_default_user(
    mock_transcription_service,
    mock_memory_service,
):
    """Test that the default user ID is dev-user."""

    override_services(
        mock_transcription_service,
        mock_memory_service,
    )

    response = client.post(
        "/memories/voice",
        files={
            "audio": (
                "test.mp3",
                b"fake audio content",
                "audio/mpeg",
            )
        },
    )

    assert response.status_code == 201

    call_kwargs = mock_memory_service.create_memory.call_args.kwargs

    assert call_kwargs["user_id"] == "dev-user"


def test_create_voice_memory_transcription_error(
    mock_transcription_service,
    mock_memory_service,
):
    """Test transcription service errors."""

    mock_transcription_service.transcribe = AsyncMock(
        side_effect=TranscriptionError(
            "Transcription service unavailable"
        )
    )

    override_services(
        mock_transcription_service,
        mock_memory_service,
    )

    response = client.post(
        "/memories/voice",
        files={
            "audio": (
                "test.mp3",
                b"fake audio content",
                "audio/mpeg",
            )
        },
    )

    assert response.status_code == 500

    data = response.json()

    assert "Transcription failed" in data["detail"]

    mock_memory_service.create_memory.assert_not_called()


def test_create_voice_memory_empty_transcription(
    mock_transcription_service,
    mock_memory_service,
):
    """Test empty transcription result."""

    mock_transcription_service.transcribe = AsyncMock(
        return_value=""
    )

    override_services(
        mock_transcription_service,
        mock_memory_service,
    )

    response = client.post(
        "/memories/voice",
        files={
            "audio": (
                "test.mp3",
                b"fake audio content",
                "audio/mpeg",
            )
        },
    )

    assert response.status_code == 422

    data = response.json()

    assert data["detail"] == "Transcription returned empty result"

    mock_memory_service.create_memory.assert_not_called()


def test_create_voice_memory_empty_audio(
    mock_transcription_service,
    mock_memory_service,
):
    """Test empty audio file."""

    mock_transcription_service.transcribe = AsyncMock(
        side_effect=TranscriptionError(
            "No audio file provided"
        )
    )

    override_services(
        mock_transcription_service,
        mock_memory_service,
    )

    response = client.post(
        "/memories/voice",
        files={
            "audio": (
                "test.mp3",
                b"",
                "audio/mpeg",
            )
        },
    )

    assert response.status_code == 400

    data = response.json()

    assert "No audio file" in data["detail"]

    mock_memory_service.create_memory.assert_not_called()


def test_create_voice_memory_unsupported_format(
    mock_transcription_service,
    mock_memory_service,
):
    """Test unsupported audio format."""

    mock_transcription_service.transcribe = AsyncMock(
        side_effect=TranscriptionError(
            "Unsupported audio format"
        )
    )

    override_services(
        mock_transcription_service,
        mock_memory_service,
    )

    response = client.post(
        "/memories/voice",
        files={
            "audio": (
                "test.txt",
                b"not an audio file",
                "text/plain",
            )
        },
    )

    assert response.status_code == 400

    data = response.json()

    assert "Unsupported" in data["detail"]

    mock_memory_service.create_memory.assert_not_called()


def test_create_voice_memory_file_too_large(
    mock_transcription_service,
    mock_memory_service,
):
    """Test audio file size validation."""

    mock_transcription_service.transcribe = AsyncMock(
        side_effect=TranscriptionError(
            "Audio file is too large"
        )
    )

    override_services(
        mock_transcription_service,
        mock_memory_service,
    )

    response = client.post(
        "/memories/voice",
        files={
            "audio": (
                "large.mp3",
                b"fake large audio content",
                "audio/mpeg",
            )
        },
    )

    assert response.status_code == 413

    data = response.json()

    assert "too large" in data["detail"].lower()

    mock_memory_service.create_memory.assert_not_called()


def test_create_voice_memory_database_error(
    mock_transcription_service,
    mock_memory_service,
):
    """Test database error while creating memory."""

    mock_memory_service.create_memory = Mock(
        side_effect=SQLAlchemyError("DB Error")
    )

    override_services(
        mock_transcription_service,
        mock_memory_service,
    )

    response = client.post(
        "/memories/voice",
        files={
            "audio": (
                "test.mp3",
                b"fake audio content",
                "audio/mpeg",
            )
        },
    )

    assert response.status_code == 500

    data = response.json()

    assert data["detail"] == "Database error while creating memory"


def test_create_voice_memory_memory_service_error(
    mock_transcription_service,
    mock_memory_service,
):
    """Test generic memory service error."""

    mock_memory_service.create_memory = Mock(
        side_effect=Exception("Unexpected memory error")
    )

    override_services(
        mock_transcription_service,
        mock_memory_service,
    )

    response = client.post(
        "/memories/voice",
        files={
            "audio": (
                "test.mp3",
                b"fake audio content",
                "audio/mpeg",
            )
        },
    )

    assert response.status_code == 500

    data = response.json()

    assert "Failed to process memory" in data["detail"]
