import logging
from fastapi import APIRouter, Depends, HTTPException, status, Header, Query
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.search.search_service import SearchService
from app.search.schemas import SemanticSearchRequest, SemanticSearchResponse


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