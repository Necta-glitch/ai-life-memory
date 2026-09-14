import pytest
from unittest.mock import Mock
from httpx import AsyncClient

from app.search.search_service import SearchService
from app.search.schemas import SemanticSearchResponse, SemanticSearchResult


class TestSearchAPI:
    @pytest.fixture
    def mock_search_service(self):
        return Mock(spec=SearchService)

    @pytest.fixture
    def sample_search_response(self):
        return SemanticSearchResponse(
            results=[
                SemanticSearchResult(
                    id=1,
                    user_id="dev-user",
                    content="Learned about RRF",
                    summary="User learned about RRF",
                    topics=["RRF", "search"],
                    entities=["RRF", "Python"],
                    source="text",
                    created_at="2024-01-15T10:00:00",
                    occurred_at=None,
                    similarity=0.92,
                )
            ],
            query="RRF search",
            total_candidates=10,
        )

    @pytest.mark.asyncio
    async def test_semantic_search_success(
        self, client: AsyncClient, mock_search_service, sample_search_response
    ):
        mock_search_service.semantic_search.return_value = sample_search_response

        # Override the search_service in the API
        from app.api.search import search_service as api_search_service
        api_search_service.semantic_search = mock_search_service.semantic_search

        response = await client.post(
            "/search/semantic",
            json={"query": "RRF search", "top_k": 5},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["query"] == "RRF search"
        assert len(data["results"]) == 1
        assert data["results"][0]["similarity"] == 0.92
        assert data["total_candidates"] == 10

    @pytest.mark.asyncio
    async def test_semantic_search_empty_results(
        self, client: AsyncClient, mock_search_service
    ):
        empty_response = SemanticSearchResponse(
            results=[],
            query="unknown",
            total_candidates=0,
        )
        mock_search_service.semantic_search.return_value = empty_response

        from app.api.search import search_service as api_search_service
        api_search_service.semantic_search = mock_search_service.semantic_search

        response = await client.post(
            "/search/semantic",
            json={"query": "unknown", "top_k": 5},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["results"] == []
        assert data["total_candidates"] == 0

    @pytest.mark.asyncio
    async def test_semantic_search_invalid_query_empty(
        self, client: AsyncClient
    ):
        response = await client.post(
            "/search/semantic",
            json={"query": "", "top_k": 5},
        )

        assert response.status_code == 422  # Validation error

    @pytest.mark.asyncio
    async def test_semantic_search_invalid_top_k_too_high(
        self, client: AsyncClient
    ):
        response = await client.post(
            "/search/semantic",
            json={"query": "test", "top_k": 100},
        )

        assert response.status_code == 422  # Validation error

    @pytest.mark.asyncio
    async def test_semantic_search_invalid_top_k_zero(
        self, client: AsyncClient
    ):
        response = await client.post(
            "/search/semantic",
            json={"query": "test", "top_k": 0},
        )

        assert response.status_code == 422  # Validation error

    @pytest.mark.asyncio
    async def test_semantic_search_default_top_k(
        self, client: AsyncClient, mock_search_service, sample_search_response
    ):
        mock_search_service.semantic_search.return_value = sample_search_response

        from app.api.search import search_service as api_search_service
        api_search_service.semantic_search = mock_search_service.semantic_search

        response = await client.post(
            "/search/semantic",
            json={"query": "test"},
        )

        assert response.status_code == 200
        # Verify the service was called with default top_k=10
        call_args = mock_search_service.semantic_search.call_args
        request_arg = call_args.kwargs["request"]
        assert request_arg.top_k == 10

    @pytest.mark.asyncio
    async def test_semantic_search_user_isolation(
        self, client: AsyncClient, mock_search_service, sample_search_response
    ):
        mock_search_service.semantic_search.return_value = sample_search_response

        from app.api.search import search_service as api_search_service
        api_search_service.semantic_search = mock_search_service.semantic_search

        response = await client.post(
            "/search/semantic",
            json={"query": "test"},
            headers={"X-User-ID": "user-b"},
        )

        assert response.status_code == 200
        call_args = mock_search_service.semantic_search.call_args
        assert call_args.kwargs["user_id"] == "user-b"

    @pytest.mark.asyncio
    async def test_semantic_search_error_handling(
        self, client: AsyncClient, mock_search_service
    ):
        from openai import APIError
        import httpx

        request = httpx.Request("POST", "https://api.openai.com/v1/embeddings")
        mock_search_service.semantic_search.side_effect = APIError("API Error", request=request, body=None)

        from app.api.search import search_service as api_search_service
        api_search_service.semantic_search = mock_search_service.semantic_search

        response = await client.post(
            "/search/semantic",
            json={"query": "test"},
        )

        assert response.status_code == 500