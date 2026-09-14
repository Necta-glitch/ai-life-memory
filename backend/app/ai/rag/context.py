from app.ai.rag.schemas import RAGContext, RAGContextItem, build_rag_context
from app.search.schemas import HybridSearchResult


def build_context_from_hybrid_results(
    query: str,
    hybrid_results: list[HybridSearchResult],
) -> RAGContext:
    """
    Build RAG context from hybrid search results.
    
    This is the main entry point for converting hybrid search results
    into a structured RAG context ready for LLM consumption.
    
    Args:
        query: The original user query
        hybrid_results: List of HybridSearchResult from hybrid search
        
    Returns:
        RAGContext with structured items
    """
    return build_rag_context(query, hybrid_results)


def format_context_for_llm(context: RAGContext) -> str:
    """
    Format RAG context as a deterministic text string for LLM consumption.
    
    Args:
        context: Structured RAG context
        
    Returns:
        Formatted text string with all memories clearly separated
    """
    return context.to_text()