"""Voice memory API endpoints."""

import logging
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, Header, HTTPException, UploadFile, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from app.db.database import get_db
from app.services.memory_service import MemoryService
from app.schemas.memory import MemoryCreate, MemoryResponse
from app.ai.transcription_service import TranscriptionService, TranscriptionError

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/memories", tags=["memories"])


def get_user_id(
    user_id: str = "dev-user",
    x_user_id: Optional[str] = Header(None, alias="X-User-ID"),
) -> str:
    """Get user ID from query param or header."""
    return x_user_id if x_user_id is not None else user_id


def get_transcription_service() -> TranscriptionService:
    """Dependency for TranscriptionService to allow mocking in tests."""
    return TranscriptionService()


def get_memory_service() -> MemoryService:
    """Dependency for MemoryService to allow mocking in tests."""
    return MemoryService()


@router.post("/voice", response_model=MemoryResponse, status_code=status.HTTP_201_CREATED)
async def create_voice_memory(
    audio: UploadFile = File(...),
    occurred_at: Optional[datetime] = Form(None),
    db: Session = Depends(get_db),
    user_id: str = Depends(get_user_id),
    transcription_service: TranscriptionService = Depends(get_transcription_service),
    memory_service: MemoryService = Depends(get_memory_service),
):
    """
    Create a memory from voice audio.

    Upload an audio file to transcribe and save as a memory.

    Args:
        audio: Audio file (max 25 MB, formats: mp3, mp4, wav, webm, m4a, ogg, flac)
        occurred_at: Optional timestamp when the memory occurred

    Returns:
        Created memory with transcription as content

    Raises:
        400: Invalid audio file (missing, too large, unsupported format)
        422: Empty transcription result
        500: Transcription or database error
    """
    try:
        # Transcribe audio (includes validation)
        try:
            transcript = await transcription_service.transcribe(audio)
        except TranscriptionError as e:
            # Convert validation errors to appropriate HTTP status codes
            error_msg = str(e)
            if "too large" in error_msg.lower():
                raise HTTPException(
                    status_code=status.HTTP_413_CONTENT_TOO_LARGE,
                    detail=error_msg,
                )
            elif "unsupported" in error_msg.lower() or "format" in error_msg.lower():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=error_msg,
                )
            elif "no audio file" in error_msg.lower() or "empty" in error_msg.lower() or "filename" in error_msg.lower():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=error_msg,
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Transcription failed: {error_msg}",
                )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Transcription failed: {str(e)}",
            )

        if not transcript or not transcript.strip():
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Transcription returned empty result",
            )

        # Create memory with transcribed content
        memory_create = MemoryCreate(
            content=transcript.strip(),
            source="voice",
            occurred_at=occurred_at,
        )

        # Save memory using existing pipeline
        try:
            memory = memory_service.create_memory(
                db=db,
                memory=memory_create,
                user_id=user_id,
            )
        except SQLAlchemyError:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Database error while creating memory",
            )
        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to process memory: {str(e)}",
            )

        return memory

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Unexpected error creating voice memory")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )