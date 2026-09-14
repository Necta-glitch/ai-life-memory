import pytest
from unittest.mock import Mock, patch, MagicMock
from sqlalchemy.orm import Session

from app.ai.rag.service import RAGService
from app.ai.rag.schemas import (
    RAGContext, RAGContextItem, RAGSource, 
    RAGAnswerRequest, RAGAnswerResponse
)
from app.ai.rag.context import build_context_from_hybrid_results
from app.search.schemas import HybridSearchResult
from app.search.search_service import SearchService
from datetime import datetime, UTC


class TestRAGAnswerSchemas:
    def test_rag_answer_request_valid(self):
        request = RAGAnswerRequest(query="test query", top_k=5)
        assert request.query == "test query"
        assert request.top_k == 5

    def test_rag_answer_request_default_top_k(self):
        request = RAGAnswerRequest(query="test query")
        assert request.top_k == 10

    def test_rag_answer_request_invalid_query(self):
        with pytest.raises(ValueError):
            RAGAnswerRequest(query="")

    def test_rag_answer_request_top_k_bounds(self):
        with pytest.raises(ValueError):
            RAGAnswerRequest(query="test", top_k=0)
        with pytest.raises(ValueError):
            RAGAnswerRequest(query="test", top_k=51)

    def test_rag_source(self):
        source = RAGSource(memory_id=1, rrf_score=0.0325)
        assert source.memory_id == 1
        assert source.rrf_score == 0.0325

    def test_rag_answer_response(self):
        response = RAGAnswerResponse(
            answer="Test answer",
            sources=[RAGSource(memory_id=1, rrf_score=0.0325)],
            query="test query",
            total_sources=1,
        )
        assert response.answer == "Test answer"
        assert len(response.sources) == 1
        assert response.sources[0].memory_id == 1
        assert response.total_sources == 1


class TestRAGService:
    @pytest.fixture
    def mock_search_service(self):
        return Mock(spec=SearchService)

    @pytest.fixture
    def mock_embedding_service(self):
        return Mock()

    @pytest.fixture
    def rag_service(self, mock_search_service, mock_embedding_service):
        with patch("app.ai.rag.service.OpenAI") as mock_openai_class:
            mock_client = Mock()
            mock_openai_class.return_value = mock_client
            
            service = RAGService(
                search_service=mock_search_service,
                api_key="test-key",
                model="gpt-4o-mini",
            )
            yield service

    @pytest.fixture
    def mock_db(self):
        return Mock(spec=Session)

    @pytest.fixture
    def sample_hybrid_results(self):
        return [
            HybridSearchResult(
                id=1,
                user_id="dev-user",
                content="Hoy aprendí sobre RRF para combinar rankings.",
                summary="Learned about RRF for combining rankings.",
                topics=["RRF", "search", "hybrid"],
                entities=["RRF", "Python"],
                source="text",
                created_at="2026-09-13T14:17:11.967778",
                occurred_at=None,
                rrf_score=0.03278688524590164,
            ),
            HybridSearchResult(
                id=2,
                user_id="dev-user",
                content="Implementé búsqueda semántica con pgvector.",
                summary="Implemented semantic search with pgvector.",
                topics=["semantic search", "pgvector", "embeddings"],
                entities=["PostgreSQL", "pgvector"],
                source="text",
                created_at="2026-09-14T02:03:02.335218",
                occurred_at=None,
                rrf_score=0.015625,
            ),
        ]

    def test_answer_question_with_results(
        self,
        rag_service,
        mock_search_service,
        mock_db,
        sample_hybrid_results,
    ):
        # Mock hybrid search response
        mock_hybrid_response = Mock()
        mock_hybrid_response.results = sample_hybrid_results
        mock_search_service.hybrid_search.return_value = mock_hybrid_response

        # Mock LLM response
        mock_response = Mock()
        mock_choice = Mock()
        mock_choice.message.content = "Aprendiste sobre RRF (Reciprocal Rank Fusion) para combinar rankings de búsqueda semántica y por palabras clave."
        mock_response.choices = [mock_choice]
        
        rag_service.client.chat.completions.create.return_value = mock_response

        response = rag_service.answer_question(
            db=Mock(spec=Session),
            user_id="dev-user",
            query="¿Qué aprendí sobre RRF?",
            top_k=5,
        )

        assert isinstance(response, RAGAnswerResponse)
        assert "RRF" in response.answer or "Reciprocal Rank Fusion" in response.answer
        assert len(response.sources) == 2
        assert response.sources[0].memory_id == 1
        assert response.sources[1].memory_id == 2
        assert response.total_sources == 2
        assert response.query == "¿Qué aprendí sobre RRF?"

        # Verify hybrid search was called correctly
        mock_search_service.hybrid_search.assert_called_once()
        call_args = mock_search_service.hybrid_search.call_args
        assert call_args.kwargs["user_id"] == "dev-user"
        request_arg = call_args.kwargs["request"]
        assert request_arg.query == "¿Qué aprendí sobre RRF?"
        assert request_arg.top_k == 5

        # Verify LLM was called
        rag_service.client.chat.completions.create.assert_called_once()

    def test_answer_question_empty_results(
        self,
        rag_service,
        mock_search_service,
        mock_db,
    ):
        # Mock hybrid search with empty results
        mock_hybrid_response = Mock()
        mock_hybrid_response.results = []
        mock_search_service.hybrid_search.return_value = mock_hybrid_response

        response = rag_service.answer_question(
            db=Mock(spec=Session),
            user_id="dev-user",
            query="¿Qué aprendí sobre algo desconocido?",
            top_k=5,
        )

        assert isinstance(response, RAGAnswerResponse)
        assert response.answer == "No tengo memorias suficientes para responder esta pregunta."
        assert response.sources == []
        assert response.total_sources == 0
        assert response.query == "¿Qué aprendí sobre algo desconocido?"

        # Verify LLM was NOT called
        rag_service.client.chat.completions.create.assert_not_called()

    def test_answer_question_empty_query_raises(self, rag_service, mock_db):
        with pytest.raises(ValueError, match="Query cannot be empty"):
            rag_service.answer_question(
                db=Mock(spec=Session),
                user_id="dev-user",
                query="",
                top_k=5,
            )

        with pytest.raises(ValueError, match="Query cannot be empty"):
            rag_service.answer_question(
                db=Mock(spec=Session),
                user_id="dev-user",
                query="   ",
                top_k=5,
            )

    def test_answer_question_user_isolation(
        self,
        rag_service,
        mock_search_service,
        mock_db,
        sample_hybrid_results,
    ):
        mock_hybrid_response = Mock()
        mock_hybrid_response.results = sample_hybrid_results
        mock_search_service.hybrid_search.return_value = mock_hybrid_response

        mock_response = Mock()
        mock_choice = Mock()
        mock_choice.message.content = "Test answer"
        mock_response.choices = [mock_choice]
        rag_service.client.chat.completions.create.return_value = mock_response

        rag_service.answer_question(
            db=Mock(spec=Session),
            user_id="user-b",
            query="test query",
            top_k=5,
        )

        # Verify user_id passed to hybrid search
        call_args = mock_search_service.hybrid_search.call_args
        assert call_args.kwargs["user_id"] == "user-b"

    def test_answer_question_top_k_passed(
        self,
        rag_service,
        mock_search_service,
        mock_db,
        sample_hybrid_results,
    ):
        mock_hybrid_response = Mock()
        mock_hybrid_response.results = sample_hybrid_results
        mock_search_service.hybrid_search.return_value = mock_hybrid_response

        mock_response = Mock()
        mock_choice = Mock()
        mock_choice.message.content = "Test answer"
        mock_response.choices = [mock_choice]
        rag_service.client.chat.completions.create.return_value = mock_response

        rag_service.answer_question(
            db=Mock(spec=Session),
            user_id="dev-user",
            query="test query",
            top_k=3,
        )

        call_args = mock_search_service.hybrid_search.call_args
        request_arg = call_args.kwargs["request"]
        assert request_arg.top_k == 3

    def test_sources_built_from_retrieved_memories(
        self,
        rag_service,
        mock_search_service,
        mock_db,
        sample_hybrid_results,
    ):
        """Sources should be built from retrieved memories, not LLM output."""
        mock_hybrid_response = Mock()
        mock_hybrid_response.results = sample_hybrid_results
        mock_search_service.hybrid_search.return_value = mock_hybrid_response

        mock_response = Mock()
        mock_choice = Mock()
        mock_choice.message.content = "Answer with fake sources [1, 2, 3]"
        mock_response.choices = [mock_choice]
        rag_service.client.chat.completions.create.return_value = mock_response

        response = rag_service.answer_question(
            db=Mock(spec=Session),
            user_id="dev-user",
            query="test query",
            top_k=5,
        )

        # Sources should come from retrieved memories, not LLM text
        assert len(response.sources) == 2
        assert response.sources[0].memory_id == 1
        assert response.sources[1].memory_id == 2
        assert response.sources[0].rrf_score == sample_hybrid_results[0].rrf_score

    def test_answer_question_llm_error_propagates(
        self,
        rag_service,
        mock_search_service,
        mock_db,
        sample_hybrid_results,
    ):
        from openai import APIError
        import httpx

        mock_hybrid_response = Mock()
        mock_hybrid_response.results = sample_hybrid_results
        mock_search_service.hybrid_search.return_value = mock_hybrid_response

        request = httpx.Request("POST", "https://api.openai.com/v1/chat/completions")
        rag_service.client.chat.completions.create.side_effect = APIError(
            "API Error", request=request, body=None
        )

        with pytest.raises(APIError):
            rag_service.answer_question(
                db=Mock(spec=Session),
                user_id="dev-user",
                query="test query",
                top_k=5,
            )


class TestRAGAPI:
    @pytest.fixture
    def mock_rag_service(self):
        return Mock()

    @pytest.fixture
    def sample_rag_response(self):
        return RAGAnswerResponse(
            answer="Aprendiste sobre RRF para combinar rankings.",
            sources=[
                RAGSource(memory_id=1, rrf_score=0.03278688524590164),
                RAGSource(memory_id=2, rrf_score=0.015625),
            ],
            query="RRF search",
            total_sources=2,
        )

    @pytest.mark.asyncio
    async def test_chat_success(
        self, client: AsyncClient, mock_rag_service, sample_rag_response
    ):
        mock_rag_service.answer_question.return_value = sample_rag_response

        from app.api.search import rag_service as api_rag_service
        api_rag_service.answer_question = mock_rag_service.answer_question

        response = await client.post(
            "/search/chat",
            json={"query": "RRF search", "top_k": 5},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["query"] == "RRF search"
        assert "RRF" in data["answer"]
        assert len(data["sources"]) == 2
        assert data["sources"][0]["memory_id"] == 1
        assert data["total_sources"] == 2

    @pytest.mark.asyncio
    async def test_chat_empty_results(
        self, client: AsyncClient, mock_rag_service
    ):
        empty_response = RAGAnswerResponse(
            answer="No tengo memorias suficientes para responder esta pregunta.",
            sources=[],
            query="unknown",
            total_sources=0,
        )
        mock_rag_service.answer_question.return_value = empty_response

        from app.api.search import rag_service as api_rag_service
        api_rag_service.answer_question = mock_rag_service.answer_question

        response = await client.post(
            "/search/chat",
            json={"query": "unknown", "top_k": 5},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["sources"] == []
        assert data["total_sources"] == 0

    @pytest.mark.asyncio
    async def test_chat_invalid_query_empty(self, client: AsyncClient):
        response = await client.post(
            "/search/chat",
            json={"query": "", "top_k": 5},
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_chat_invalid_top_k_too_high(self, client: AsyncClient):
        response = await client.post(
            "/search/chat",
            json={"query": "test", "top_k": 100},
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_chat_invalid_top_k_zero(self, client: AsyncClient):
        response = await client.post(
            "/search/chat",
            json={"query": "test", "top_k": 0},
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_chat_default_top_k(
        self, client: AsyncClient, mock_rag_service, sample_rag_response
    ):
        mock_rag_service.answer_question.return_value = sample_rag_response

        from app.api.search import rag_service as api_rag_service
        api_rag_service.answer_question = mock_rag_service.answer_question

        response = await client.post(
            "/search/chat",
            json={"query": "test"},
        )

        assert response.status_code == 200
        call_args = mock_rag_service.answer_question.call_args
        # The function signature is answer_question(db, user_id, query, top_k)
        # query is the 3rd positional arg, top_k is 4th (or kwarg)
        if call_args.kwargs:
            assert call_args.kwargs.get("top_k", 10) == 10
        else:
            assert call_args.args[3] == 10

    @pytest.mark.asyncio
    async def test_chat_user_isolation(
        self, client: AsyncClient, mock_rag_service, sample_rag_response
    ):
        mock_rag_service.answer_question.return_value = sample_rag_response

        from app.api.search import rag_service as api_rag_service
        api_rag_service.answer_question = mock_rag_service.answer_question

        response = await client.post(
            "/search/chat",
            json={"query": "test"},
            headers={"X-User-ID": "user-b"},
        )

        assert response.status_code == 200
        call_args = mock_rag_service.answer_question.call_args
        assert call_args.kwargs["user_id"] == "user-b"

    @pytest.mark.asyncio
    async def test_chat_error_handling(self, client: AsyncClient, mock_rag_service):
        mock_rag_service.answer_question.side_effect = Exception("Database error")

        from app.api.search import rag_service as api_rag_service
        api_rag_service.answer_question = mock_rag_service.answer_question

        response = await client.post(
            "/search/chat",
            json={"query": "test"},
        )
        assert response.status_code == 500