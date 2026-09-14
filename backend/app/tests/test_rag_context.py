import pytest
from datetime import datetime, UTC
from app.ai.rag.schemas import RAGContext, RAGContextItem, build_rag_context
from app.ai.rag.context import build_context_from_hybrid_results, format_context_for_llm
from app.search.schemas import HybridSearchResult


class TestRAGContextItem:
    def test_valid_item_with_all_fields(self):
        item = RAGContextItem(
            memory_id=1,
            content="Test content",
            summary="Test summary",
            topics=["topic1", "topic2"],
            entities=["entity1"],
            occurred_at=datetime(2024, 1, 15, 10, 0, 0, tzinfo=UTC),
            created_at=datetime(2024, 1, 15, 10, 0, 0, tzinfo=UTC),
            rrf_score=0.0325,
        )
        assert item.memory_id == 1
        assert item.content == "Test content"
        assert item.summary == "Test summary"
        assert item.topics == ["topic1", "topic2"]
        assert item.entities == ["entity1"]
        assert item.rrf_score == 0.0325

    def test_item_with_minimal_fields(self):
        item = RAGContextItem(
            memory_id=1,
            content="Test content",
            created_at=datetime(2024, 1, 15, 10, 0, 0, tzinfo=UTC),
            rrf_score=0.0325,
        )
        assert item.memory_id == 1
        assert item.content == "Test content"
        assert item.summary is None
        assert item.topics == []
        assert item.entities == []
        assert item.occurred_at is None
        assert item.rrf_score == 0.0325

    def test_item_with_empty_lists(self):
        item = RAGContextItem(
            memory_id=1,
            content="Test content",
            topics=[],
            entities=[],
            created_at=datetime(2024, 1, 15, 10, 0, 0, tzinfo=UTC),
            rrf_score=0.0325,
        )
        assert item.topics == []
        assert item.entities == []


class TestRAGContext:
    def test_empty_context(self):
        context = RAGContext(query="test query", items=[], total_items=0)
        assert context.query == "test query"
        assert context.items == []
        assert context.total_items == 0

    def test_context_with_items(self):
        item = RAGContextItem(
            memory_id=1,
            content="Test content",
            created_at=datetime(2024, 1, 15, 10, 0, 0, tzinfo=UTC),
            rrf_score=0.0325,
        )
        context = RAGContext(query="test query", items=[item], total_items=1)
        assert context.total_items == 1
        assert len(context.items) == 1


class TestBuildRAGContext:
    def test_empty_results(self):
        hybrid_results = []
        context = build_rag_context("test query", hybrid_results)
        
        assert context.query == "test query"
        assert context.items == []
        assert context.total_items == 0

    def test_single_result(self):
        hybrid_results = [
            HybridSearchResult(
                id=1,
                user_id="dev-user",
                content="Test memory content",
                summary="Test summary",
                topics=["topic1", "topic2"],
                entities=["entity1"],
                source="text",
                created_at="2024-01-15T10:00:00",
                occurred_at="2024-01-15T10:00:00",
                rrf_score=0.0325,
            )
        ]
        
        context = build_rag_context("test query", hybrid_results)
        
        assert context.query == "test query"
        assert context.total_items == 1
        assert len(context.items) == 1
        assert context.items[0].memory_id == 1
        assert context.items[0].content == "Test memory content"
        assert context.items[0].summary == "Test summary"
        assert context.items[0].topics == ["topic1", "topic2"]
        assert context.items[0].entities == ["entity1"]
        assert context.items[0].rrf_score == 0.0325

    def test_multiple_results(self):
        hybrid_results = [
            HybridSearchResult(
                id=1,
                user_id="dev-user",
                content="First memory",
                summary="First summary",
                topics=["topic1"],
                entities=["entity1"],
                source="text",
                created_at="2024-01-15T10:00:00",
                occurred_at=None,
                rrf_score=0.05,
            ),
            HybridSearchResult(
                id=2,
                user_id="dev-user",
                content="Second memory",
                summary="Second summary",
                topics=["topic2"],
                entities=["entity2"],
                source="text",
                created_at="2024-01-16T10:00:00",
                occurred_at="2024-01-16T10:00:00",
                rrf_score=0.03,
            ),
        ]
        
        context = build_rag_context("test query", hybrid_results)
        
        assert context.total_items == 2
        assert len(context.items) == 2
        assert context.items[0].memory_id == 1
        assert context.items[1].memory_id == 2
        # Order preserved from input
        assert context.items[0].rrf_score == 0.05
        assert context.items[1].rrf_score == 0.03

    def test_missing_summary(self):
        hybrid_results = [
            HybridSearchResult(
                id=1,
                user_id="dev-user",
                content="Test content",
                summary=None,
                topics=[],
                entities=[],
                source="text",
                created_at="2024-01-15T10:00:00",
                occurred_at=None,
                rrf_score=0.0325,
            )
        ]
        
        context = build_rag_context("test query", hybrid_results)
        
        assert context.items[0].summary is None

    def test_missing_topics(self):
        hybrid_results = [
            HybridSearchResult(
                id=1,
                user_id="dev-user",
                content="Test content",
                summary="Summary",
                topics=None,
                entities=[],
                source="text",
                created_at="2024-01-15T10:00:00",
                occurred_at=None,
                rrf_score=0.0325,
            )
        ]
        
        context = build_rag_context("test query", hybrid_results)
        
        assert context.items[0].topics == []

    def test_missing_entities(self):
        hybrid_results = [
            HybridSearchResult(
                id=1,
                user_id="dev-user",
                content="Test content",
                summary="Summary",
                topics=[],
                entities=None,
                source="text",
                created_at="2024-01-15T10:00:00",
                occurred_at=None,
                rrf_score=0.0325,
            )
        ]
        
        context = build_rag_context("test query", hybrid_results)
        
        assert context.items[0].entities == []

    def test_missing_occurred_at(self):
        hybrid_results = [
            HybridSearchResult(
                id=1,
                user_id="dev-user",
                content="Test content",
                summary="Summary",
                topics=[],
                entities=[],
                source="text",
                created_at="2024-01-15T10:00:00",
                occurred_at=None,
                rrf_score=0.0325,
            )
        ]
        
        context = build_rag_context("test query", hybrid_results)
        
        assert context.items[0].occurred_at is None

    def test_topics_formatting(self):
        hybrid_results = [
            HybridSearchResult(
                id=1,
                user_id="dev-user",
                content="Test content",
                summary="Summary",
                topics=["topic1", "topic2", "topic3"],
                entities=[],
                source="text",
                created_at="2024-01-15T10:00:00",
                occurred_at=None,
                rrf_score=0.0325,
            )
        ]
        
        context = build_rag_context("test query", hybrid_results)
        
        assert context.items[0].topics == ["topic1", "topic2", "topic3"]

    def test_entities_formatting(self):
        hybrid_results = [
            HybridSearchResult(
                id=1,
                user_id="dev-user",
                content="Test content",
                summary="Summary",
                topics=[],
                entities=["entity1", "entity2"],
                source="text",
                created_at="2024-01-15T10:00:00",
                occurred_at=None,
                rrf_score=0.0325,
            )
        ]
        
        context = build_rag_context("test query", hybrid_results)
        
        assert context.items[0].entities == ["entity1", "entity2"]

    def test_embedding_excluded(self):
        """Verify embeddings are never included in generated context."""
        hybrid_results = [
            HybridSearchResult(
                id=1,
                user_id="dev-user",
                content="Test content",
                summary="Summary",
                topics=[],
                entities=[],
                source="text",
                created_at="2024-01-15T10:00:00",
                occurred_at=None,
                rrf_score=0.0325,
            )
        ]
        
        context = build_rag_context("test query", hybrid_results)
        
        # Check that the item doesn't have an embedding field
        item_dict = context.items[0].model_dump()
        assert "embedding" not in item_dict
        # Also verify the model doesn't define embedding
        assert "embedding" not in RAGContextItem.model_fields

    def test_deterministic_output(self):
        """Given the same input, output must be exactly identical."""
        hybrid_results = [
            HybridSearchResult(
                id=1,
                user_id="dev-user",
                content="Test content",
                summary="Summary",
                topics=["topic1"],
                entities=["entity1"],
                source="text",
                created_at="2024-01-15T10:00:00",
                occurred_at="2024-01-15T10:00:00",
                rrf_score=0.0325,
            )
        ]
        
        context1 = build_rag_context("test query", hybrid_results)
        context2 = build_rag_context("test query", hybrid_results)
        
        # Compare model dumps for exact equality
        assert context1.model_dump() == context2.model_dump()

    def test_special_characters_preserved(self):
        hybrid_results = [
            HybridSearchResult(
                id=1,
                user_id="dev-user",
                content="Content with \"quotes\", newlines\nand accents: áéíóú",
                summary="Summary with special chars: \"quotes\" and 'apostrophes'",
                topics=["topic with spaces"],
                entities=["entity with, commas"],
                source="text",
                created_at="2024-01-15T10:00:00",
                occurred_at=None,
                rrf_score=0.0325,
            )
        ]
        
        context = build_rag_context("test query", hybrid_results)
        
        assert '\"quotes\"' in context.items[0].content
        assert "newlines\nand accents" in context.items[0].content
        assert "áéíóú" in context.items[0].content
        assert '\"quotes\"' in context.items[0].summary
        assert "'apostrophes'" in context.items[0].summary


class TestFormatContextForLLM:
    def test_empty_context(self):
        context = RAGContext(query="test query", items=[], total_items=0)
        text = format_context_for_llm(context)
        
        assert "test query" in text
        assert "No relevant memories found" in text

    def test_single_memory_format(self):
        item = RAGContextItem(
            memory_id=1,
            content="Test content",
            summary="Test summary",
            topics=["topic1", "topic2"],
            entities=["entity1"],
            occurred_at=datetime(2024, 1, 15, 10, 0, 0, tzinfo=UTC),
            created_at=datetime(2024, 1, 15, 10, 0, 0, tzinfo=UTC),
            rrf_score=0.0325,
        )
        context = RAGContext(query="test query", items=[item], total_items=1)
        text = format_context_for_llm(context)
        
        assert "Query: test query" in text
        assert "Memory 1:" in text
        assert "ID: 1" in text
        assert "Content: Test content" in text
        assert "Summary: Test summary" in text
        assert "Topics: topic1, topic2" in text
        assert "Entities: entity1" in text
        assert "Occurred: 2024-01-15T10:00:00+00:00" in text
        assert "Created: 2024-01-15T10:00:00+00:00" in text
        assert "RRF Score: 0.032500" in text

    def test_multiple_memories_format(self):
        item1 = RAGContextItem(
            memory_id=1,
            content="First memory",
            summary="First summary",
            topics=["topic1"],
            entities=["entity1"],
            occurred_at=None,
            created_at=datetime(2024, 1, 15, 10, 0, 0, tzinfo=UTC),
            rrf_score=0.05,
        )
        item2 = RAGContextItem(
            memory_id=2,
            content="Second memory",
            summary="Second summary",
            topics=["topic2"],
            entities=["entity2"],
            occurred_at=datetime(2024, 1, 16, 10, 0, 0, tzinfo=UTC),
            created_at=datetime(2024, 1, 16, 10, 0, 0, tzinfo=UTC),
            rrf_score=0.03,
        )
        context = RAGContext(query="test query", items=[item1, item2], total_items=2)
        text = format_context_for_llm(context)
        
        assert "Memory 1:" in text
        assert "Memory 2:" in text
        assert "ID: 1" in text
        assert "ID: 2" in text
        assert "First memory" in text
        assert "Second memory" in text

    def test_optional_fields_not_included_when_none(self):
        item = RAGContextItem(
            memory_id=1,
            content="Test content",
            summary=None,
            topics=[],
            entities=[],
            occurred_at=None,
            created_at=datetime(2024, 1, 15, 10, 0, 0, tzinfo=UTC),
            rrf_score=0.0325,
        )
        context = RAGContext(query="test query", items=[item], total_items=1)
        text = format_context_for_llm(context)
        
        assert "Summary:" not in text
        assert "Topics:" not in text
        assert "Entities:" not in text
        assert "Occurred:" not in text


class TestBuildContextFromHybridResults:
    def test_integration_with_hybrid_search_result(self):
        hybrid_results = [
            HybridSearchResult(
                id=1,
                user_id="dev-user",
                content="Test content",
                summary="Test summary",
                topics=["topic1"],
                entities=["entity1"],
                source="text",
                created_at="2024-01-15T10:00:00",
                occurred_at="2024-01-15T10:00:00",
                rrf_score=0.0325,
            )
        ]
        
        context = build_context_from_hybrid_results("test query", hybrid_results)
        
        assert isinstance(context, RAGContext)
        assert context.query == "test query"
        assert context.total_items == 1
        assert context.items[0].memory_id == 1