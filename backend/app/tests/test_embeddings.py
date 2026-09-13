import pytest
from app.ai.embeddings import build_embedding_input
from app.models.memory import Memory


class TestBuildEmbeddingInput:
    """Tests for build_embedding_input function."""

    # Strategy: content
    def test_content_only_strategy(self):
        result = build_embedding_input(
            content="Learned about Python async",
            summary="User learned about async programming",
            topics=["Python", "async"],
            entities=["Python", "asyncio"],
            strategy="content",
        )
        assert result == "Learned about Python async"

    def test_content_only_ignores_other_fields(self):
        result = build_embedding_input(
            content="Content only",
            summary="Should be ignored",
            topics=["ignored"],
            entities=["ignored"],
            strategy="content",
        )
        assert result == "Content only"

    # Strategy: content_summary (default)
    def test_content_summary_default_strategy(self):
        result = build_embedding_input(
            content="Learned about Python async",
            summary="User learned about async programming",
        )
        assert result == "Learned about Python async\n\nUser learned about async programming"

    def test_content_summary_explicit_strategy(self):
        result = build_embedding_input(
            content="Learned about Python async",
            summary="User learned about async programming",
            strategy="content_summary",
        )
        assert result == "Learned about Python async\n\nUser learned about async programming"

    def test_content_summary_with_none_summary(self):
        result = build_embedding_input(
            content="Content only",
            summary=None,
            strategy="content_summary",
        )
        assert result == "Content only"

    def test_content_summary_with_empty_summary(self):
        result = build_embedding_input(
            content="Content only",
            summary="",
            strategy="content_summary",
        )
        assert result == "Content only"

    def test_content_summary_with_whitespace_summary(self):
        result = build_embedding_input(
            content="Content",
            summary="   ",
            strategy="content_summary",
        )
        assert result == "Content"

    # Strategy: full
    def test_full_strategy_with_all_fields(self):
        result = build_embedding_input(
            content="Learned about RRF",
            summary="User learned about RRF",
            topics=["RRF", "search", "hybrid"],
            entities=["RRF", "Python"],
            strategy="full",
        )
        expected = "Learned about RRF\n\nUser learned about RRF\n\nTopics: RRF, search, hybrid\n\nEntities: RRF, Python"
        assert result == expected

    def test_full_strategy_with_none_fields(self):
        result = build_embedding_input(
            content="Content only",
            summary=None,
            topics=None,
            entities=None,
            strategy="full",
        )
        assert result == "Content only"

    def test_full_strategy_with_empty_lists(self):
        result = build_embedding_input(
            content="Content",
            summary="Summary",
            topics=[],
            entities=[],
            strategy="full",
        )
        assert result == "Content\n\nSummary"

    def test_full_strategy_filters_empty_items(self):
        result = build_embedding_input(
            content="Content",
            summary="Summary",
            topics=["RRF", "", "  ", "search"],
            entities=["Python", "   "],
            strategy="full",
        )
        expected = "Content\n\nSummary\n\nTopics: RRF, search\n\nEntities: Python"
        assert result == expected

    # Input validation
    def test_empty_content_raises(self):
        with pytest.raises(ValueError, match="Content cannot be empty"):
            build_embedding_input(content="", summary="Summary", strategy="content_summary")

    def test_whitespace_content_raises(self):
        with pytest.raises(ValueError, match="Content cannot be empty"):
            build_embedding_input(content="   ", summary="Summary", strategy="content_summary")

    def test_invalid_strategy_raises(self):
        with pytest.raises(ValueError, match="Invalid strategy"):
            build_embedding_input(content="Content", strategy="invalid")

    def test_none_content_raises(self):
        with pytest.raises(ValueError, match="Content cannot be empty"):
            build_embedding_input(content=None, summary="Summary", strategy="content_summary")  # type: ignore

    # Whitespace handling
    def test_strips_content_whitespace(self):
        result = build_embedding_input(
            content="  Content with spaces  ",
            strategy="content",
        )
        assert result == "Content with spaces"

    def test_strips_summary_whitespace(self):
        result = build_embedding_input(
            content="Content",
            summary="  Summary with spaces  ",
            strategy="content_summary",
        )
        assert result == "Content\n\nSummary with spaces"

    def test_strips_topics_entities_whitespace(self):
        result = build_embedding_input(
            content="Content",
            summary="Summary",
            topics=["  Python  ", "async  "],
            entities=["  RRF  "],
            strategy="full",
        )
        expected = "Content\n\nSummary\n\nTopics: Python, async\n\nEntities: RRF"
        assert result == expected


class TestMemoryEmbeddingModel:
    """Tests for Memory model embedding field."""

    def test_embedding_field_accepts_1536_dim_vector(self):
        """Verify the embedding field can store a 1536-dimensional vector."""
        vector_1536 = [0.1] * 1536
        memory = Memory(
            user_id="test-user",
            content="Test content",
            embedding=vector_1536,
        )
        assert memory.embedding == vector_1536
        assert len(memory.embedding) == 1536

    def test_embedding_field_accepts_none(self):
        """Verify the embedding field can be None (nullable)."""
        memory = Memory(
            user_id="test-user",
            content="Test content",
            embedding=None,
        )
        assert memory.embedding is None

    def test_embedding_field_accepts_empty_list(self):
        """Verify the embedding field can be an empty list."""
        memory = Memory(
            user_id="test-user",
            content="Test content",
            embedding=[],
        )
        assert memory.embedding == []

    def test_embedding_field_accepts_smaller_vector(self):
        """Verify the embedding field can store vectors of different sizes (SQLite JSON)."""
        vector_384 = [0.5] * 384
        memory = Memory(
            user_id="test-user",
            content="Test content",
            embedding=vector_384,
        )
        assert memory.embedding == vector_384
        assert len(memory.embedding) == 384