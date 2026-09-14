import pytest
from app.search.schemas import HybridSearchRequest, HybridSearchResult, HybridSearchResponse


class TestHybridSearchRequest:
    def test_valid_request(self):
        request = HybridSearchRequest(query="test query", top_k=5)
        assert request.query == "test query"
        assert request.top_k == 5

    def test_default_top_k(self):
        request = HybridSearchRequest(query="test query")
        assert request.top_k == 10

    def test_invalid_query_empty(self):
        with pytest.raises(ValueError):
            HybridSearchRequest(query="")

    def test_invalid_query_whitespace(self):
        request = HybridSearchRequest(query="   ")
        assert request.query == "   "

    def test_top_k_too_low(self):
        with pytest.raises(ValueError):
            HybridSearchRequest(query="test", top_k=0)

    def test_top_k_too_high(self):
        with pytest.raises(ValueError):
            HybridSearchRequest(query="test", top_k=51)

    def test_query_max_length(self):
        with pytest.raises(ValueError):
            HybridSearchRequest(query="x" * 1001)


class TestHybridSearchResult:
    def test_valid_result(self):
        result = HybridSearchResult(
            id=1,
            user_id="dev-user",
            content="Test content",
            summary="Test summary",
            topics=["test"],
            entities=["test"],
            source="text",
            created_at="2024-01-01T00:00:00",
            occurred_at="2024-01-01T00:00:00",
            rrf_score=0.0325,
        )
        assert result.rrf_score == 0.0325
        assert result.id == 1


class TestHybridSearchResponse:
    def test_valid_response(self):
        results = [
            HybridSearchResult(
                id=1,
                user_id="dev-user",
                content="Test",
                summary=None,
                topics=None,
                entities=None,
                source="text",
                created_at="2024-01-01T00:00:00",
                rrf_score=0.0325,
            )
        ]
        response = HybridSearchResponse(
            results=results,
            query="test",
            total_candidates=10,
        )
        assert len(response.results) == 1
        assert response.query == "test"
        assert response.total_candidates == 10