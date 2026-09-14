from pydantic import BaseModel, Field


class SemanticSearchRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=1000, description="Search query text")
    top_k: int = Field(default=10, ge=1, le=50, description="Number of results to return")


class SemanticSearchResult(BaseModel):
    id: int
    user_id: str
    content: str
    summary: str | None = None
    topics: list[str] | None = None
    entities: list[str] | None = None
    source: str
    created_at: str
    occurred_at: str | None = None
    similarity: float = Field(..., ge=0.0, le=1.0, description="Cosine similarity (0-1, higher = more similar)")


class SemanticSearchResponse(BaseModel):
    results: list[SemanticSearchResult]
    query: str
    total_candidates: int


class KeywordSearchRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=1000, description="Search query text")
    top_k: int = Field(default=10, ge=1, le=50, description="Number of results to return")


class KeywordSearchResult(BaseModel):
    id: int
    user_id: str
    content: str
    summary: str | None = None
    topics: list[str] | None = None
    entities: list[str] | None = None
    source: str
    created_at: str
    occurred_at: str | None = None
    keyword_score: float = Field(..., ge=0.0, description="PostgreSQL ts_rank relevance score (higher = more relevant)")


class KeywordSearchResponse(BaseModel):
    results: list[KeywordSearchResult]
    query: str
    total_candidates: int


class HybridSearchRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=1000, description="Search query text")
    top_k: int = Field(default=10, ge=1, le=50, description="Number of results to return")


class HybridSearchResult(BaseModel):
    id: int
    user_id: str
    content: str
    summary: str | None = None
    topics: list[str] | None = None
    entities: list[str] | None = None
    source: str
    created_at: str
    occurred_at: str | None = None
    rrf_score: float = Field(..., ge=0.0, description="RRF fusion score (higher = more relevant)")
    rerank_score: float | None = Field(default=None, ge=-1.0, le=1.0, description="Reranking cosine similarity score (higher = more relevant)")
    embedding: list[float] | None = Field(default=None, description="Memory embedding vector (1536 dimensions)")


class HybridSearchResponse(BaseModel):
    results: list[HybridSearchResult]
    query: str
    total_candidates: int