def build_embedding_input(
    content: str,
    summary: str | None = None,
    topics: list[str] | None = None,
    entities: list[str] | None = None,
    strategy: str = "content_summary",
) -> str:
    """
    Construct text for embedding based on strategy.
    
    Args:
        content: Original memory content (required)
        summary: AI-generated summary (optional)
        topics: Extracted topics (optional)
        entities: Extracted entities (optional)
        strategy: Embedding strategy to use:
            - "content": content only
            - "content_summary": content + summary (default)
            - "full": content + summary + topics + entities
        
    Returns:
        Text to embed
        
    Raises:
        ValueError: If content is empty or strategy is invalid
    """
    if not content or not content.strip():
        raise ValueError("Content cannot be empty")
    
    valid_strategies = ("content", "content_summary", "full")
    if strategy not in valid_strategies:
        raise ValueError(f"Invalid strategy: {strategy}. Must be one of {valid_strategies}")
    
    parts = [content.strip()]
    
    if strategy in ("content_summary", "full") and summary and summary.strip():
        parts.append(summary.strip())
    
    if strategy == "full":
        if topics:
            topics_str = ", ".join(t.strip() for t in topics if t and t.strip())
            if topics_str:
                parts.append(f"Topics: {topics_str}")
        if entities:
            entities_str = ", ".join(e.strip() for e in entities if e and e.strip())
            if entities_str:
                parts.append(f"Entities: {entities_str}")
    
    return "\n\n".join(parts)