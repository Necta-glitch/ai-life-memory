"""Tests for the transcription service."""

import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from fastapi import UploadFile

from app.ai.transcription_service import TranscriptionService, TranscriptionError
from app.core.config import OPENAI_TRANSCRIPTION_MODEL


class TestTranscriptionService:
    """Tests for TranscriptionService."""

    @pytest.fixture
    def mock_openai_class(self):
        with patch("app.ai.transcription_service.OpenAI") as mock_openai_class:
            mock_client = Mock()
            mock_openai_class.return_value = mock_client
            yield mock_openai_class

    @pytest.fixture
    def mock_openai_client(self, mock_openai_class):
        """Provide the mock client instance for tests that need it."""
        return mock_openai_class.return_value

    @pytest.fixture
    def transcription_service(self, mock_openai_class):
        service = TranscriptionService(api_key="test-key", model="whisper-1")
        return service

    def test_init_with_explicit_params(self):
        service = TranscriptionService(api_key="explicit-key", model="whisper-1")
        assert service.api_key == "explicit-key"
        assert service.model == "whisper-1"

    def test_init_uses_config_defaults(self):
        with patch("app.ai.transcription_service.OPENAI_API_KEY", "config-key"), \
             patch("app.ai.transcription_service.OPENAI_TRANSCRIPTION_MODEL", "config-model"):
            service = TranscriptionService()
            assert service.api_key == "config-key"
            assert service.model == "config-model"

    def test_client_property_creates_client_once(self, transcription_service, mock_openai_class):
        mock_client = Mock()
        mock_openai_class.return_value = mock_client

        client1 = transcription_service.client
        client2 = transcription_service.client
        assert client1 is client2
        assert client1 is mock_client
        mock_openai_class.assert_called_once_with(api_key="test-key")

    def test_client_property_raises_without_api_key(self):
        with patch("app.ai.transcription_service.OPENAI_API_KEY", None):
            service = TranscriptionService(api_key=None)
            with pytest.raises(ValueError, match="OPENAI_API_KEY is not configured"):
                _ = service.client

    def test_validate_audio_missing(self, transcription_service):
        with pytest.raises(TranscriptionError, match="No audio file provided"):
            transcription_service._validate_audio(None)

    def test_validate_audio_missing_filename(self, transcription_service):
        mock_audio = Mock(spec=UploadFile)
        mock_audio.filename = None
        mock_audio.content_type = "audio/mpeg"
        mock_audio.size = 1000

        with pytest.raises(TranscriptionError, match="Audio file must have a filename"):
            transcription_service._validate_audio(mock_audio)

    def test_validate_audio_unsupported_content_type(self, transcription_service):
        mock_audio = Mock(spec=UploadFile)
        mock_audio.filename = "test.txt"
        mock_audio.content_type = "text/plain"
        mock_audio.size = 1000

        with pytest.raises(TranscriptionError, match="Unsupported audio format"):
            transcription_service._validate_audio(mock_audio)

    def test_validate_audio_file_too_large(self, transcription_service):
        mock_audio = Mock(spec=UploadFile)
        mock_audio.filename = "test.mp3"
        mock_audio.content_type = "audio/mpeg"
        mock_audio.size = 30 * 1024 * 1024  # 30 MB

        with pytest.raises(TranscriptionError, match="Audio file too large"):
            transcription_service._validate_audio(mock_audio)

    def test_validate_audio_valid(self, transcription_service):
        mock_audio = Mock(spec=UploadFile)
        mock_audio.filename = "test.mp3"
        mock_audio.content_type = "audio/mpeg"
        mock_audio.size = 1000

        # Should not raise
        transcription_service._validate_audio(mock_audio)

    @pytest.mark.asyncio
    async def test_transcribe_success(self, transcription_service, mock_openai_client):
        mock_response = "This is a test transcription."
        mock_openai_client.audio.transcriptions.create.return_value = mock_response

        mock_audio = Mock(spec=UploadFile)
        mock_audio.filename = "test.mp3"
        mock_audio.content_type = "audio/mpeg"
        mock_audio.size = 1000
        mock_audio.read = AsyncMock(return_value=b"fake audio content")
        mock_audio.seek = AsyncMock()

        transcript = await transcription_service.transcribe(mock_audio)

        assert transcript == "This is a test transcription."
        mock_openai_client.audio.transcriptions.create.assert_called_once()
        call_args = mock_openai_client.audio.transcriptions.create.call_args
        assert call_args.kwargs["model"] == "whisper-1"
        assert call_args.kwargs["response_format"] == "text"

    @pytest.mark.asyncio
    async def test_transcribe_empty_audio(self, transcription_service):
        mock_audio = Mock(spec=UploadFile)
        mock_audio.filename = "test.mp3"
        mock_audio.content_type = "audio/mpeg"
        mock_audio.size = 1000
        mock_audio.read = AsyncMock(return_value=b"")
        mock_audio.seek = AsyncMock()

        with pytest.raises(TranscriptionError, match="Audio file is empty"):
            await transcription_service.transcribe(mock_audio)

    @pytest.mark.asyncio
    async def test_transcribe_empty_transcription_result(self, transcription_service, mock_openai_client):
        mock_openai_client.audio.transcriptions.create.return_value = ""

        mock_audio = Mock(spec=UploadFile)
        mock_audio.filename = "test.mp3"
        mock_audio.content_type = "audio/mpeg"
        mock_audio.size = 1000
        mock_audio.read = AsyncMock(return_value=b"fake audio content")
        mock_audio.seek = AsyncMock()

        with pytest.raises(TranscriptionError, match="Transcription returned empty result"):
            await transcription_service.transcribe(mock_audio)

    @pytest.mark.asyncio
    async def test_transcribe_openai_error_propagates(self, transcription_service, mock_openai_client):
        from openai import APIError
        import httpx

        request = httpx.Request("POST", "https://api.openai.com/v1/audio/transcriptions")
        mock_openai_client.audio.transcriptions.create.side_effect = APIError(
            "API Error", request=request, body=None
        )

        mock_audio = Mock(spec=UploadFile)
        mock_audio.filename = "test.mp3"
        mock_audio.content_type = "audio/mpeg"
        mock_audio.size = 1000
        mock_audio.read = AsyncMock(return_value=b"fake audio content")
        mock_audio.seek = AsyncMock()

        with pytest.raises(TranscriptionError, match="Transcription failed"):
            await transcription_service.transcribe(mock_audio)

    @pytest.mark.asyncio
    async def test_transcribe_unsupported_content_type(self, transcription_service):
        mock_audio = Mock(spec=UploadFile)
        mock_audio.filename = "test.txt"
        mock_audio.content_type = "text/plain"
        mock_audio.size = 1000

        with pytest.raises(TranscriptionError, match="Unsupported audio format"):
            await transcription_service.transcribe(mock_audio)

    @pytest.mark.asyncio
    async def test_transcribe_file_too_large(self, transcription_service):
        mock_audio = Mock(spec=UploadFile)
        mock_audio.filename = "test.mp3"
        mock_audio.content_type = "audio/mpeg"
        mock_audio.size = 30 * 1024 * 1024  # 30 MB

        with pytest.raises(TranscriptionError, match="Audio file too large"):
            await transcription_service.transcribe(mock_audio)

    @pytest.mark.asyncio
    async def test_transcribe_missing_audio(self, transcription_service):
        with pytest.raises(TranscriptionError, match="No audio file provided"):
            await transcription_service.transcribe(None)

    @pytest.mark.asyncio
    async def test_transcribe_empty_file(self, transcription_service):
        mock_audio = Mock(spec=UploadFile)
        mock_audio.filename = "test.mp3"
        mock_audio.content_type = "audio/mpeg"
        mock_audio.size = 1000
        mock_audio.read = AsyncMock(return_value=b"")
        mock_audio.seek = AsyncMock()

        with pytest.raises(TranscriptionError, match="Audio file is empty"):
            await transcription_service.transcribe(mock_audio)