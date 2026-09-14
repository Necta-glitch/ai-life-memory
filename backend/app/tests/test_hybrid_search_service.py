import pytest
from unittest.mock import Mock, MagicMock
from sqlalchemy.orm import Session

from app.search.search_service import SearchService
from app.search.schemas import (
    HybridSearchRequest,
    HybridSearchResponse,
    HybridSearchResult,
    SemanticSearchRequest,
    SemanticSearchResponse,
    SemanticSearchResult,
    KeywordSearchRequest,
    KeywordSearchResponse,
    KeywordSearchResult,
)
from app.repositories.search_repository import SearchRepository
from app.ai.embedding_service import EmbeddingService
from app.models.memory import Memory
from datetime import datetime, UTC


class TestRRFScoring:
    """Tests for RRF score calculation logic."""

    @pytest.fixture
    def search_service(self):
        return SearchService()

    def test_rrf_single_semantic_rank_1(self, search_service):
        """Document at rank 1 in semantic only."""
        semantic = [
            SemanticSearchResult(
                id=1, user_id="dev-user", content="A", summary=None,
                topics=[], entities=[], source="text",
                created_at="2024-01-01T00:00:00", similarity=0.9
            )
        ]
        keyword = []
        
        scores = search_service._get_rrf_scores(semantic, keyword)
        assert scores == {1: 1.0 / 61}

    def test_rrf_single_keyword_rank_1(self, search_service):
        """Document at rank 1 in keyword only."""
        semantic = []
        keyword = [
            KeywordSearchResult(
                id=1, user_id="dev-user", content="A", summary=None,
                topics=[], entities=[], source="text",
                created_at="2024-01-01T00:00:00", keyword_score=0.9
            )
        ]
        
        scores = search_service._get_rrf_scores(semantic, keyword)
        assert scores == {1: 1.0 / 61}

    def test_rrf_semantic_rank_1_keyword_rank_2(self, search_service):
        """Document appears in both: semantic #1, keyword #2."""
        semantic = [
            SemanticSearchResult(
                id=1, user_id="dev-user", content="A", summary=None,
                topics=[], entities=[], source="text",
                created_at="2024-01-01T00:00:00", similarity=0.9
            )
        ]
        keyword = [
            KeywordSearchResult(
                id=2, user_id="dev-user", content="B", summary=None,
                topics=[], entities=[], source="text",
                created_at="2024-01-01T00:00:00", keyword_score=0.8
            ),
            KeywordSearchResult(
                id=1, user_id="dev-user", content="A", summary=None,
                topics=[], entities=[], source="text",
                created_at="2024-01-01T00:00:00", keyword_score=0.7
            ),
        ]
        
        scores = search_service._get_rrf_scores(semantic, keyword)
        # A: semantic rank 1 (1/61) + keyword rank 2 (1/62)
        assert scores[1] == 1.0/61 + 1.0/62
        # B: keyword rank 1 (1/61)
        assert scores[2] == 1.0/61

    def test_rrf_multiple_documents_both_rankings(self, search_service):
        """Test the deterministic example from requirements:
        Semantic: A #1, B #2, C #3
        Keyword:  C #1, A #2, D #3
        """
        semantic = [
            SemanticSearchResult(id=1, user_id="dev-user", content="A", summary=None,
                topics=[], entities=[], source="text",
                created_at="2024-01-01T00:00:00", similarity=0.9),
            SemanticSearchResult(id=2, user_id="dev-user", content="B", summary=None,
                topics=[], entities=[], source="text",
                created_at="2024-01-01T00:00:00", similarity=0.8),
            SemanticSearchResult(id=3, user_id="dev-user", content="C", summary=None,
                topics=[], entities=[], source="text",
                created_at="2024-01-01T00:00:00", similarity=0.7),
        ]
        keyword = [
            KeywordSearchResult(id=3, user_id="dev-user", content="C", summary=None,
                topics=[], entities=[], source="text",
                created_at="2024-01-01T00:00:00", keyword_score=0.9),
            KeywordSearchResult(id=1, user_id="dev-user", content="A", summary=None,
                topics=[], entities=[], source="text",
                created_at="2024-01-01T00:00:00", keyword_score=0.8),
            KeywordSearchResult(id=4, user_id="dev-user", content="D", summary=None,
                topics=[], entities=[], source="text",
                created_at="2024-01-01T00:00:00", keyword_score=0.6),
        ]
        
        scores = search_service._get_rrf_scores(semantic, keyword)
        
        # A: semantic #1 (1/61) + keyword #2 (1/62) = 0.01639 + 0.01613 = 0.03252
        # B: semantic #2 (1/62) = 0.01613
        # C: semantic #3 (1/63) + keyword #1 (1/61) = 0.01587 + 0.01639 = 0.03226
        # D: keyword #3 (1/63) = 0.01587
        
        expected_a = 1.0/61 + 1.0/62
        expected_b = 1.0/62
        expected_c = 1.0/63 + 1.0/61
        expected_d = 1.0/63
        
        assert abs(scores[1] - expected_a) < 1e-10
        assert abs(scores[2] - expected_b) < 1e-10
        assert abs(scores[3] - expected_c) < 1e-10
        assert abs(scores[4] - expected_d) < 1e-10
        
        # Order should be: A > C > B > D
        sorted_ids = sorted(scores.keys(), key=lambda mid: scores[mid], reverse=True)
        assert sorted_ids == [1, 3, 2, 4]

    def test_rrf_accumulates_contributions(self, search_service):
        """Verify duplicate IDs accumulate, not overwrite."""
        semantic = [
            SemanticSearchResult(id=1, user_id="dev-user", content="A", summary=None,
                topics=[], entities=[], source="text",
                created_at="2024-01-01T00:00:00", similarity=0.9),
            SemanticSearchResult(id=1, user_id="dev-user", content="A dup", summary=None,
                topics=[], entities=[], source="text",
                created_at="2024-01-01T00:00:00", similarity=0.8),
        ]
        keyword = []
        
        scores = search_service._get_rrf_scores(semantic, keyword)
        # Should have both ranks 1 and 2 for same ID
        assert scores[1] == 1.0/61 + 1.0/62

    def test_rrf_empty_results(self, search_service):
        """Empty results from both searches."""
        scores = search_service._get_rrf_scores([], [])
        assert scores == {}

    def test_rrf_k_parameter(self, search_service):
        """Test custom k value."""
        semantic = [
            SemanticSearchResult(id=1, user_id="dev-user", content="A", summary=None,
                topics=[], entities=[], source="text",
                created_at="2024-01-01T00:00:00", similarity=0.9)
        ]
        keyword = []
        
        scores = search_service._get_rrf_scores(semantic, keyword, k=10)
        assert scores == {1: 1.0 / 11}


class TestHybridSearchService:
    @pytest.fixture
    def mock_search_repository(self):
        return Mock(spec=SearchRepository)

    @pytest.fixture
    def mock_embedding_service(self):
        return Mock(spec=EmbeddingService)

    @pytest.fixture
    def search_service(self, mock_search_repository, mock_embedding_service):
        return SearchService(
            embedding_service=mock_embedding_service,
            search_repository=mock_search_repository,
        )

    @pytest.fixture
    def mock_db(self):
        db = Mock(spec=Session)
        # Mock the db.execute().scalar() for total_candidates in semantic_search
        mock_result = Mock()
        mock_result.scalar.return_value = 10
        db.execute.return_value = mock_result
        return db

    @pytest.fixture
    def sample_memories(self):
        return [
            Memory(
                id=1, user_id="dev-user", content="A about RRF", summary="Summary A",
                topics=["RRF"], entities=["RRF"], source="text",
                created_at=datetime.now(UTC), occurred_at=datetime.now(UTC),
            ),
            Memory(
                id=2, user_id="dev-user", content="B about search", summary="Summary B",
                topics=["search"], entities=["Python"], source="text",
                created_at=datetime.now(UTC), occurred_at=datetime.now(UTC),
            ),
            Memory(
                id=3, user_id="dev-user", content="C about keyword", summary="Summary C",
                topics=["keyword"], entities=[], source="text",
                created_at=datetime.now(UTC), occurred_at=datetime.now(UTC),
            ),
            Memory(
                id=4, user_id="dev-user", content="D other", summary="Summary D",
                topics=[], entities=[], source="text",
                created_at=datetime.now(UTC), occurred_at=datetime.now(UTC),
            ),
        ]

    def test_hybrid_search_success(
        self,
        search_service,
        mock_search_repository,
        mock_embedding_service,
        mock_db,
        sample_memories,
    ):
        # Mock embedding service
        mock_embedding_service.get_embedding.return_value = [0.1] * 1536
        
        # Mock search repository to return different rankings
        # Semantic: A #1, B #2
        # Keyword: B #1, C #2
        mock_search_repository.search_by_vector.return_value = [
            (sample_memories[0], 0.2),  # A - distance 0.2
            (sample_memories[1], 0.3),  # B - distance 0.3
        ]
        mock_search_repository.search_by_keyword.return_value = [
            (sample_memories[1], 0.8),  # B - keyword_score 0.8
            (sample_memories[2], 0.7),  # C - keyword_score 0.7
        ]
        mock_search_repository.count_keyword_candidates.return_value = 3

        request = HybridSearchRequest(query="RRF search", top_k=5)
        response = search_service.hybrid_search(db=mock_db, request=request, user_id="dev-user")

        assert isinstance(response, HybridSearchResponse)
        assert response.query == "RRF search"
        assert len(response.results) <= 5
        assert response.total_candidates > 0

    def test_hybrid_search_respects_top_k(
        self,
        search_service,
        mock_embedding_service,
        mock_db,
    ):
        mock_embedding_service.get_embedding.return_value = [0.1] * 1536
        
        # Create enough mock results
        memories = [
            Memory(id=i, user_id="dev-user", content=f"Memory {i}", summary=None,
                topics=[], entities=[], source="text",
                created_at=datetime.now(UTC), occurred_at=datetime.now(UTC))
            for i in range(1, 11)
        ]
        
        # Return 10 results from each search
        from app.repositories.search_repository import SearchRepository
        mock_repo = Mock(spec=SearchRepository)
        mock_repo.search_by_vector.return_value = [(m, 0.1) for m in memories[:5]]
        mock_repo.search_by_keyword.return_value = [(m, 0.9) for m in memories[5:]]
        mock_repo.count_keyword_candidates.return_value = 10
        
        # Create service with mocked repo
        service = SearchService(embedding_service=Mock(spec=EmbeddingService), search_repository=mock_repo)
        service.embedding_service.get_embedding.return_value = [0.1] * 1536
        
        request = HybridSearchRequest(query="test", top_k=3)
        response = service.hybrid_search(db=mock_db, request=request, user_id="dev-user")

        assert len(response.results) == 3

    def test_hybrid_search_total_candidates_unique(
        self,
        search_service,
        mock_embedding_service,
        mock_db,
    ):
        """total_candidates should count unique IDs across both searches."""
        mock_embedding_service.get_embedding.return_value = [0.1] * 1536
        
        # Semantic: A, B, C
        # Keyword: C, D, E
        # Unique: A, B, C, D, E = 5
        memories_a = [Memory(id=i, user_id="dev-user", content=f"Mem {i}", summary=None,
            topics=[], entities=[], source="text",
            created_at=datetime.now(UTC), occurred_at=datetime.now(UTC)) for i in [1, 2, 3]]
        memories_b = [Memory(id=i, user_id="dev-user", content=f"Mem {i}", summary=None,
            topics=[], entities=[], source="text",
            created_at=datetime.now(UTC), occurred_at=datetime.now(UTC)) for i in [3, 4, 5]]
        
        mock_repo = Mock(spec=SearchRepository)
        mock_repo.search_by_vector.return_value = [(m, 0.1) for m in memories_a]
        mock_repo.search_by_keyword.return_value = [(m, 0.9) for m in memories_b]
        mock_repo.count_keyword_candidates.return_value = 3
        
        service = SearchService(embedding_service=Mock(spec=EmbeddingService), search_repository=mock_repo)
        service.embedding_service.get_embedding.return_value = [0.1] * 1536
        
        request = HybridSearchRequest(query="test", top_k=10)
        response = service.hybrid_search(db=mock_db, request=request, user_id="dev-user")

        assert response.total_candidates == 5  # A, B, C, D, E


class TestHybridSearchAPI:
    @pytest.fixture
    def mock_search_service(self):
        return Mock(spec=SearchService)

    @pytest.fixture
    def sample_hybrid_response(self):
        return HybridSearchResponse(
            results=[
                HybridSearchResult(
                    id=1,
                    user_id="dev-user",
                    content="Learned about RRF and keyword search",
                    summary="User learned about RRF for hybrid search",
                    topics=["RRF", "search", "hybrid"],
                    entities=["RRF", "Python"],
                    source="text",
                    created_at="2024-01-15T10:00:00",
                    occurred_at=None,
                    rrf_score=0.0325,
                )
            ],
            query="RRF keyword",
            total_candidates=5,
        )

    @pytest.mark.asyncio
    async def test_hybrid_search_success(
        self, client: AsyncClient, mock_search_service, sample_hybrid_response
    ):
        mock_search_service.hybrid_search.return_value = sample_hybrid_response

        from app.api.search import search_service as api_search_service
        api_search_service.hybrid_search = mock_search_service.hybrid_search

        response = await client.post(
            "/search/hybrid",
            json={"query": "RRF keyword", "top_k": 5},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["query"] == "RRF keyword"
        assert len(data["results"]) == 1
        assert data["results"][0]["rrf_score"] == 0.0325
        assert data["total_candidates"] == 5

    @pytest.mark.asyncio
    async def test_hybrid_search_empty_results(
        self, client: AsyncClient, mock_search_service
    ):
        empty_response = HybridSearchResponse(
            results=[],
            query="unknown",
            total_candidates=0,
        )
        mock_search_service.hybrid_search.return_value = empty_response

        from app.api.search import search_service as api_search_service
        api_search_service.hybrid_search = mock_search_service.hybrid_search

        response = await client.post(
            "/search/hybrid",
            json={"query": "unknown", "top_k": 5},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["results"] == []
        assert data["total_candidates"] == 0

    @pytest.mark.asyncio
    async def test_hybrid_search_invalid_query_empty(
        self, client: AsyncClient
    ):
        response = await client.post(
            "/search/hybrid",
            json={"query": "", "top_k": 5},
        )

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_hybrid_search_invalid_top_k_too_high(
        self, client: AsyncClient
    ):
        response = await client.post(
            "/search/hybrid",
            json={"query": "test", "top_k": 100},
        )

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_hybrid_search_invalid_top_k_zero(
        self, client: AsyncClient
    ):
        response = await client.post(
            "/search/hybrid",
            json={"query": "test", "top_k": 0},
        )

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_hybrid_search_default_top_k(
        self, client: AsyncClient, mock_search_service, sample_hybrid_response
    ):
        mock_search_service.hybrid_search.return_value = sample_hybrid_response

        from app.api.search import search_service as api_search_service
        api_search_service.hybrid_search = mock_search_service.hybrid_search

        response = await client.post(
            "/search/hybrid",
            json={"query": "test"},
        )

        assert response.status_code == 200
        call_args = mock_search_service.hybrid_search.call_args
        request_arg = call_args.kwargs["request"]
        assert request_arg.top_k == 10

    @pytest.mark.asyncio
    async def test_hybrid_search_user_isolation(
        self, client: AsyncClient, mock_search_service, sample_hybrid_response
    ):
        mock_search_service.hybrid_search.return_value = sample_hybrid_response

        from app.api.search import search_service as api_search_service
        api_search_service.hybrid_search = mock_search_service.hybrid_search

        response = await client.post(
            "/search/hybrid",
            json={"query": "test"},
            headers={"X-User-ID": "user-b"},
        )

        assert response.status_code == 200
        call_args = mock_search_service.hybrid_search.call_args
        assert call_args.kwargs["user_id"] == "user-b"

    @pytest.mark.asyncio
    async def test_hybrid_search_error_handling(
        self, client: AsyncClient, mock_search_service
    ):
        mock_search_service.hybrid_search.side_effect = Exception("Database error")

        from app.api.search import search_service as api_search_service
        api_search_service.hybrid_search = mock_search_service.hybrid_search

        response = await client.post(
            "/search/hybrid",
            json={"query": "test"},
        )

        assert response.status_code == 500