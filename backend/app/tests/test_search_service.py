import pytest
from unittest.mock import Mock, patch
from sqlalchemy.orm import Session

from app.search.search_service import SearchService
from app.search.schemas import SemanticSearchRequest, SemanticSearchResponse, SemanticSearchResult
from app.ai.embedding_service import EmbeddingService
from app.repositories.search_repository import SearchRepository
from app.models.memory import Memory
from datetime import datetime, UTC


class TestSearchService:
    @pytest.fixture
    def mock_embedding_service(self):
        return Mock(spec=EmbeddingService)

    @pytest.fixture
    def mock_search_repository(self):
        return Mock(spec=SearchRepository)

    @pytest.fixture
    def search_service(self, mock_embedding_service, mock_search_repository):
        return SearchService(
            embedding_service=mock_embedding_service,
            search_repository=mock_search_repository,
        )

    @pytest.fixture
    def mock_db(self):
        return Mock(spec=Session)

    @pytest.fixture
    def sample_memory(self):
        memory = Memory(
            id=1,
            user_id="dev-user",
            content="Learned about RRF",
            summary="User learned about RRF",
            topics=["RRF", "search"],
            entities=["RRF", "Python"],
            source="text",
            created_at=datetime.now(UTC),
            occurred_at=datetime.now(UTC),
        )
        return memory

    def test_semantic_search_success(
        self,
        search_service,
        mock_embedding_service,
        mock_search_repository,
        mock_db,
        sample_memory,
    ):
        # Setup mocks
        mock_embedding_service.get_embedding.return_value = [0.1] * 1536
        mock_search_repository.search_by_vector.return_value = [
            (sample_memory, 0.2),  # cosine distance
        ]
        mock_db.execute.return_value.scalar.return_value = 5  # total candidates

        request = SemanticSearchRequest(query="RRF search", top_k=5)
        response = search_service.semantic_search(db=mock_db, request=request, user_id="dev-user")

        assert isinstance(response, SemanticSearchResponse)
        assert response.query == "RRF search"
        assert len(response.results) == 1
        assert response.results[0].id == 1
        assert response.results[0].similarity == 0.8  # 1 - 0.2
        assert response.total_candidates == 5

        mock_embedding_service.get_embedding.assert_called_once_with("RRF search")
        mock_search_repository.search_by_vector.assert_called_once_with(
            db=mock_db,
            query_embedding=[0.1] * 1536,
            user_id="dev-user",
            top_k=5,
        )

    def test_semantic_search_empty_results(
        self,
        search_service,
        mock_embedding_service,
        mock_search_repository,
        mock_db,
    ):
        mock_embedding_service.get_embedding.return_value = [0.1] * 1536
        mock_search_repository.search_by_vector.return_value = []
        mock_db.execute.return_value.scalar.return_value = 0

        request = SemanticSearchRequest(query="unknown topic", top_k=10)
        response = search_service.semantic_search(db=mock_db, request=request, user_id="dev-user")

        assert len(response.results) == 0
        assert response.total_candidates == 0

    def test_semantic_search_multiple_results_ordered(
        self,
        search_service,
        mock_embedding_service,
        mock_search_repository,
        mock_db,
        sample_memory,
    ):
        # Results come ordered by distance ascending (most similar first)
        mock_embedding_service.get_embedding.return_value = [0.1] * 1536
        mock_search_repository.search_by_vector.return_value = [
            (sample_memory, 0.1),  # most similar
            (Memory(
                id=2,
                user_id="dev-user",
                content="Other memory",
                summary="Other",
                topics=[],
                entities=[],
                source="text",
                created_at=datetime.now(UTC),
                occurred_at=datetime.now(UTC),
            ), 0.5),  # less similar
        ]
        mock_db.execute.return_value.scalar.return_value = 2

        request = SemanticSearchRequest(query="test", top_k=10)
        response = search_service.semantic_search(db=mock_db, request=request, user_id="dev-user")

        assert len(response.results) == 2
        assert response.results[0].similarity == 0.9  # 1 - 0.1
        assert response.results[1].similarity == 0.5  # 1 - 0.5
        # Results should be ordered by similarity descending (most similar first)
        assert response.results[0].similarity > response.results[1].similarity

    def test_semantic_search_empty_query_raises(self, search_service, mock_db):
        mock_embedding_service = search_service.embedding_service
        mock_embedding_service.get_embedding.side_effect = ValueError("Text cannot be empty")

        request = SemanticSearchRequest(query="test", top_k=10)
        mock_embedding_service.get_embedding.side_effect = ValueError("Text cannot be empty")
        with pytest.raises(ValueError, match="Text cannot be empty"):
            search_service.semantic_search(db=mock_db, request=request, user_id="dev-user")

    def test_semantic_search_embedding_error_propagates(
        self,
        search_service,
        mock_embedding_service,
        mock_db,
    ):
        from openai import APIError
        import httpx

        request = httpx.Request("POST", "https://api.openai.com/v1/embeddings")
        mock_embedding_service.get_embedding.side_effect = APIError("API Error", request=request, body=None)

        request_obj = SemanticSearchRequest(query="test", top_k=10)
        with pytest.raises(APIError):
            search_service.semantic_search(db=mock_db, request=request_obj, user_id="dev-user")

    def test_semantic_search_respects_top_k(
        self,
        search_service,
        mock_embedding_service,
        mock_search_repository,
        mock_db,
        sample_memory,
    ):
        mock_embedding_service.get_embedding.return_value = [0.1] * 1536
        mock_search_repository.search_by_vector.return_value = [(sample_memory, 0.2)]
        mock_db.execute.return_value.scalar.return_value = 1

        request = SemanticSearchRequest(query="test", top_k=3)
        search_service.semantic_search(db=mock_db, request=request, user_id="dev-user")

        mock_search_repository.search_by_vector.assert_called_once()
        call_kwargs = mock_search_repository.search_by_vector.call_args.kwargs
        assert call_kwargs["top_k"] == 3