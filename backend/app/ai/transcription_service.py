"""Audio transcription service using OpenAI Whisper."""

from typing import Optional

from fastapi import UploadFile
from openai import OpenAI

from app.core.config import OPENAI_API_KEY, OPENAI_TRANSCRIPTION_MODEL


# Supported audio MIME types for OpenAI Whisper
SUPPORTED_AUDIO_TYPES = {
    "audio/mpeg",      # mp3
    "audio/mp3",       # mp3
    "audio/wav",       # wav
    "audio/x-wav",     # wav
    "audio/mp4",       # m4a, mp4
    "audio/m4a",       # m4a
    "audio/webm",      # webm
    "audio/ogg",       # ogg
    "audio/flac",      # flac
}

MAX_AUDIO_SIZE = 25 * 1024 * 1024  # 25 MB (OpenAI limit)


class TranscriptionError(Exception):
    """Raised when transcription fails."""

    def __init__(
        self, 
        message: str, 
        original_error: Optional[Exception] = None,
        request: Optional[object] = None,
        body: Optional[object] = None,
    ):
        super().__init__(message)
        self.original_error = original_error
        self.request = request
        self.body = body


class TranscriptionService:
    """Service for transcribing audio files using OpenAI Whisper."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
    ):
        self.api_key = api_key or OPENAI_API_KEY
        self.model = model or OPENAI_TRANSCRIPTION_MODEL
        self._client: Optional[OpenAI] = None

    @property
    def client(self) -> OpenAI:
        if self._client is None:
            if not self.api_key:
                raise ValueError("OPENAI_API_KEY is not configured")
            self._client = OpenAI(api_key=self.api_key)
        return self._client

    def _validate_audio(self, audio: UploadFile) -> None:
        """Validate audio file before transcription."""
        if not audio:
            raise TranscriptionError("No audio file provided")

        if not audio.filename:
            raise TranscriptionError("Audio file must have a filename")

        # Check content type
        content_type = audio.content_type or ""
        if content_type not in SUPPORTED_AUDIO_TYPES:
            raise TranscriptionError(
                f"Unsupported audio format: {content_type}. "
                f"Supported formats: {', '.join(sorted(SUPPORTED_AUDIO_TYPES))}"
            )

        # Check file size
        if audio.size is not None and audio.size > MAX_AUDIO_SIZE:
            raise TranscriptionError(
                f"Audio file too large: {audio.size} bytes. Maximum size: {MAX_AUDIO_SIZE} bytes (25 MB)"
            )

    async def transcribe(self, audio: UploadFile) -> str:
        """
        Transcribe audio file to text using OpenAI Whisper.

        Args:
            audio: The audio file to transcribe

        Returns:
            The transcribed text

        Raises:
            TranscriptionError: If transcription fails
        """
        self._validate_audio(audio)

        # Read audio content
        audio_content = await audio.read()
        if not audio_content:
            raise TranscriptionError("Audio file is empty")

        # Reset file pointer for potential re-read
        await audio.seek(0)

        try:
            # Create a file-like object for the OpenAI API
            import io
            audio_file = io.BytesIO(audio_content)
            audio_file.name = audio.filename or "audio.wav"

            # Call OpenAI Whisper API
            response = self.client.audio.transcriptions.create(
                model=self.model,
                file=audio_file,
                response_format="text",
            )

            transcript = response.strip()
            if not transcript:
                raise TranscriptionError("Transcription returned empty result")

            return transcript

        except TranscriptionError:
            raise
        except Exception as e:
            raise TranscriptionError(f"Transcription failed: {str(e)}", original_error=e)