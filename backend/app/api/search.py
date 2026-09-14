import logging
from fastapi import APIRouter, Depends, HTTPException, status, Header, Query
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.search.search_service import SearchService
from app.ai.rag.service import RAGService
from app.search.schemas import (
    SemanticSearchRequest, 
    SemanticSearchResponse,
    KeywordSearchRequest,
    KeywordSearchResponse,
    HybridSearchRequest,
    HybridSearchResponse,
)
from app.ai.rag.schemas import RAGAnswerRequest, RAGAnswerResponse


router = APIRouter(prefix="/search", tags=["search"])
search_service = SearchService()
rag_service = RAGService()

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


@router.post("/chat", response_model=RAGAnswerResponse, tags=["chat"])
def chat(
    request: RAGAnswerRequest,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_user_id),
):
    """
    Generate a grounded answer using RAG (Retrieval-Augmented Generation).
    
    Performs hybrid search, builds RAG context, and generates a grounded answer.
    """
    try:
        return rag_service.answer_question(
            db=db,
            user_id=user_id,
            query=request.query,
            top_k=request.top_k,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.exception("Chat failed for user=%s query=%s", user_id, request.query)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Chat failed",
        )


@router.post("/rerank", response_model=HybridSearchResponse)
def rerank_search(
    request: HybridSearchRequest,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_user_id),
):
    """
    Perform hybrid search with reranking by embedding similarity.
    
    This endpoint performs:
    1. Hybrid search (semantic + keyword + RRF) to get a candidate pool
    2. Reranking by cosine similarity between query and memory embeddings
    
    Returns memories ordered by reranking score (cosine similarity).
    """
    try:
        return search_service.hybrid_search_with_rerank(
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
        logger.exception("Rerank search failed for user=%s query=%s", user_id, request.query)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Rerank search failed",
        )