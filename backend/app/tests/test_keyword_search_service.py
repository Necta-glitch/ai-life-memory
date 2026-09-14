import pytest
from unittest.mock import Mock
from sqlalchemy.orm import Session

from app.search.search_service import SearchService
from app.search.schemas import KeywordSearchRequest, KeywordSearchResponse, KeywordSearchResult
from app.repositories.search_repository import SearchRepository
from app.models.memory import Memory
from datetime import datetime, UTC


class TestKeywordSearchService:
    @pytest.fixture
    def mock_search_repository(self):
        return Mock(spec=SearchRepository)

    @pytest.fixture
    def search_service(self, mock_search_repository):
        return SearchService(search_repository=mock_search_repository)

    @pytest.fixture
    def mock_db(self):
        return Mock(spec=Session)

    @pytest.fixture
    def sample_memory(self):
        memory = Memory(
            id=1,
            user_id="dev-user",
            content="Learned about RRF and keyword search",
            summary="User learned about RRF for hybrid search",
            topics=["RRF", "search", "hybrid"],
            entities=["RRF", "Python"],
            source="text",
            created_at=datetime.now(UTC),
            occurred_at=datetime.now(UTC),
        )
        return memory

    def test_keyword_search_success(
        self,
        search_service,
        mock_search_repository,
        mock_db,
        sample_memory,
    ):
        # Setup mocks
        mock_search_repository.search_by_keyword.return_value = [
            (sample_memory, 0.85),
        ]
        mock_search_repository.count_keyword_candidates.return_value = 3

        request = KeywordSearchRequest(query="RRF keyword", top_k=5)
        response = search_service.keyword_search(db=mock_db, request=request, user_id="dev-user")

        assert isinstance(response, KeywordSearchResponse)
        assert response.query == "RRF keyword"
        assert len(response.results) == 1
        assert response.results[0].id == 1
        assert response.results[0].keyword_score == 0.85
        assert response.total_candidates == 3

        mock_search_repository.search_by_keyword.assert_called_once_with(
            db=mock_db,
            query="RRF keyword",
            user_id="dev-user",
            top_k=5,
        )
        mock_search_repository.count_keyword_candidates.assert_called_once_with(
            db=mock_db,
            query="RRF keyword",
            user_id="dev-user",
        )

    def test_keyword_search_empty_results(
        self,
        search_service,
        mock_search_repository,
        mock_db,
    ):
        mock_search_repository.search_by_keyword.return_value = []
        mock_search_repository.count_keyword_candidates.return_value = 0

        request = KeywordSearchRequest(query="unknown topic", top_k=10)
        response = search_service.keyword_search(db=mock_db, request=request, user_id="dev-user")

        assert len(response.results) == 0
        assert response.total_candidates == 0

    def test_keyword_search_multiple_results_ordered(
        self,
        search_service,
        mock_search_repository,
        mock_db,
        sample_memory,
    ):
        # Results come ordered by rank descending (most relevant first)
        mock_search_repository.search_by_keyword.return_value = [
            (sample_memory, 0.9),  # most relevant
            (Memory(
                id=2,
                user_id="dev-user",
                content="Other memory about search",
                summary="Other search memory",
                topics=[],
                entities=[],
                source="text",
                created_at=datetime.now(UTC),
                occurred_at=datetime.now(UTC),
            ), 0.3),  # less relevant
        ]
        mock_search_repository.count_keyword_candidates.return_value = 2

        request = KeywordSearchRequest(query="search", top_k=10)
        response = search_service.keyword_search(db=mock_db, request=request, user_id="dev-user")

        assert len(response.results) == 2
        assert response.results[0].keyword_score == 0.9
        assert response.results[1].keyword_score == 0.3
        # Results should be ordered by keyword_score descending (most relevant first)
        assert response.results[0].keyword_score > response.results[1].keyword_score

    def test_keyword_search_respects_top_k(
        self,
        search_service,
        mock_search_repository,
        mock_db,
        sample_memory,
    ):
        mock_search_repository.search_by_keyword.return_value = [(sample_memory, 0.8)]
        mock_search_repository.count_keyword_candidates.return_value = 1

        request = KeywordSearchRequest(query="test", top_k=3)
        search_service.keyword_search(db=mock_db, request=request, user_id="dev-user")

        mock_search_repository.search_by_keyword.assert_called_once()
        call_kwargs = mock_search_repository.search_by_keyword.call_args.kwargs
        assert call_kwargs["top_k"] == 3

    def test_keyword_search_without_embedding(self, search_service, mock_search_repository, mock_db, sample_memory):
        """Memories without embeddings should still be searchable by keyword."""
        # The mock doesn't care about embeddings - keyword search doesn't depend on them
        mock_search_repository.search_by_keyword.return_value = [(sample_memory, 0.75)]
        mock_search_repository.count_keyword_candidates.return_value = 1

        request = KeywordSearchRequest(query="test", top_k=10)
        response = search_service.keyword_search(db=mock_db, request=request, user_id="dev-user")

        assert len(response.results) == 1
        assert response.results[0].keyword_score == 0.75