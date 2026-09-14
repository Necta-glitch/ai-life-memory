from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class RAGContextItem(BaseModel):
    """
    Structured representation of a memory for RAG context.
    
    Contains only the fields needed by an LLM to generate a grounded answer.
    Embeddings and internal database fields are excluded.
    """
    memory_id: int
    content: str
    summary: Optional[str] = None
    topics: list[str] = Field(default_factory=list)
    entities: list[str] = Field(default_factory=list)
    occurred_at: Optional[datetime] = None
    created_at: datetime
    rrf_score: float = Field(..., ge=0.0, description="RRF fusion score from hybrid search")


class RAGContext(BaseModel):
    """
    Complete RAG context assembled from hybrid search results.
    
    Contains the query and the structured context items ready for LLM consumption.
    """
    query: str
    items: list[RAGContextItem] = Field(default_factory=list)
    total_items: int = 0

    def to_text(self) -> str:
        """
        Convert the structured context to a deterministic text format for LLM consumption.
        
        Returns a formatted string with all memories clearly separated.
        """
        if not self.items:
            return f"Query: {self.query}\n\nNo relevant memories found."
        
        lines = [f"Query: {self.query}", ""]
        
        for i, item in enumerate(self.items, start=1):
            lines.append(f"Memory {i}:")
            lines.append(f"  ID: {item.memory_id}")
            lines.append(f"  Content: {item.content}")
            
            if item.summary:
                lines.append(f"  Summary: {item.summary}")
            
            if item.topics:
                lines.append(f"  Topics: {', '.join(item.topics)}")
            
            if item.entities:
                lines.append(f"  Entities: {', '.join(item.entities)}")
            
            if item.occurred_at:
                lines.append(f"  Occurred: {item.occurred_at.isoformat()}")
            
            lines.append(f"  Created: {item.created_at.isoformat()}")
            lines.append(f"  RRF Score: {item.rrf_score:.6f}")
            lines.append("")
        
        # Remove the last empty line
        if lines and lines[-1] == "":
            lines.pop()
        
        return "\n".join(lines)


def build_rag_context(
    query: str,
    hybrid_results: list,
) -> RAGContext:
    """
    Build RAG context from hybrid search results.
    
    Args:
        query: The original user query
        hybrid_results: List of HybridSearchResult from hybrid search
        
    Returns:
        RAGContext with structured items
    """
    items = []
    
    for result in hybrid_results:
        item = RAGContextItem(
            memory_id=result.id,
            content=result.content,
            summary=result.summary,
            topics=result.topics or [],
            entities=result.entities or [],
            occurred_at=result.occurred_at,
            created_at=result.created_at,
            rrf_score=result.rrf_score,
        )
        items.append(item)
    
    return RAGContext(
        query=query,
        items=items,
        total_items=len(items),
    )


class RAGSource(BaseModel):
    """
    Source citation for a RAG answer.
    
    Generated from retrieved memories, not from LLM output.
    """
    memory_id: int
    rrf_score: float = Field(..., ge=0.0, description="RRF fusion score from hybrid search")


class RAGAnswerRequest(BaseModel):
    """Request schema for RAG answer generation."""
    query: str = Field(..., min_length=1, max_length=1000, description="User question")
    top_k: int = Field(default=10, ge=1, le=50, description="Number of results to return")


class RAGAnswerResponse(BaseModel):
    """Response schema for RAG answer generation."""
    answer: str
    sources: list[RAGSource] = Field(default_factory=list)
    query: str
    total_sources: int