import logging
from fastapi import APIRouter, Depends, HTTPException, status, Header, Query
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.search.search_service import SearchService
from app.search.schemas import (
    SemanticSearchRequest, 
    SemanticSearchResponse,
    KeywordSearchRequest,
    KeywordSearchResponse,
    HybridSearchRequest,
    HybridSearchResponse,
)


router = APIRouter(prefix="/search", tags=["search"])
search_service = SearchService()

logger = logging.getLogger(__name__)


def get_user_id(
    user_id: str = Query(default="dev-user"),
    x_user_id: str | None = Header(default=None, alias="X-User-ID"),
) -> str:
    return x_user_id if x_user_id is not None else user_id


@router.post("/semantic", response_model=SemanticSearchResponse)
def semantic_search(
    request: SemanticSearchRequest,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_user_id),
):
    """
    Perform semantic search over the user's memories.
    
    Returns memories ordered by semantic similarity to the query.
    """
    try:
        return search_service.semantic_search(
            db=db,
            request=request,
            user_id=user_id,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.exception("Semantic search failed for user=%s query=%s", user_id, request.query)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Search failed",
        )


@router.post("/keyword", response_model=KeywordSearchResponse)
def keyword_search(
    request: KeywordSearchRequest,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_user_id),
):
    """
    Perform keyword search over the user's memories using PostgreSQL Full-Text Search.
    
    Returns memories ordered by keyword relevance (ts_rank).
    """
    try:
        return search_service.keyword_search(
            db=db,
            request=request,
            user_id=user_id,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.exception("Keyword search failed for user=%s query=%s", user_id, request.query)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Search failed",
        )


@router.post("/hybrid", response_model=HybridSearchResponse)
def hybrid_search(
    request: HybridSearchRequest,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_user_id),
):
    """
    Perform hybrid search using RRF (Reciprocal Rank Fusion) to combine
    semantic and keyword search results.
    
    Returns memories ordered by RRF fusion score.
    """
    try:
        return search_service.hybrid_search(
            db=db,
            request=request,
            user_id=user_id,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.exception("Hybrid search failed for user=%s query=%s", user_id, request.query)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Search failed",
        )