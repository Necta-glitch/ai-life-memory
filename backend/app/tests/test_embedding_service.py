import pytest
from unittest.mock import Mock, patch

from app.ai.embedding_service import EmbeddingService
from app.core.config import OPENAI_API_KEY, OPENAI_EMBEDDING_MODEL


class TestEmbeddingService:
    """Tests for EmbeddingService."""

    @pytest.fixture
    def mock_openai_class(self):
        with patch("app.ai.embedding_service.OpenAI") as mock_class:
            yield mock_class

    @pytest.fixture
    def embedding_service(self):
        return EmbeddingService(api_key="test-key", model="text-embedding-3-small")

    def test_init_with_explicit_params(self):
        service = EmbeddingService(api_key="explicit-key", model="text-embedding-3-large")
        assert service.api_key == "explicit-key"
        assert service.model == "text-embedding-3-large"

    def test_init_uses_config_defaults(self):
        with patch("app.ai.embedding_service.OPENAI_API_KEY", "config-key"), \
             patch("app.ai.embedding_service.OPENAI_EMBEDDING_MODEL", "config-model"):
            service = EmbeddingService()
            assert service.api_key == "config-key"
            assert service.model == "config-model"

    def test_client_property_creates_client_once(self, embedding_service, mock_openai_class):
        mock_client = Mock()
        mock_openai_class.return_value = mock_client
        
        client1 = embedding_service.client
        client2 = embedding_service.client
        assert client1 is client2
        assert client1 is mock_client
        mock_openai_class.assert_called_once_with(api_key="test-key")

    def test_client_property_raises_without_api_key(self):
        with patch("app.ai.embedding_service.OPENAI_API_KEY", None):
            service = EmbeddingService(api_key=None)
            with pytest.raises(ValueError, match="OPENAI_API_KEY is not configured"):
                _ = service.client

    def test_get_embedding_success(self, embedding_service, mock_openai_class):
        mock_client = Mock()
        mock_openai_class.return_value = mock_client
        
        mock_embedding = [0.1] * 1536
        mock_response = Mock()
        mock_data = Mock()
        mock_data.embedding = mock_embedding
        mock_response.data = [mock_data]
        
        mock_client.embeddings.create.return_value = mock_response

        result = embedding_service.get_embedding("Test text for embedding")

        assert isinstance(result, list)
        assert len(result) == 1536
        assert result == mock_embedding

        mock_client.embeddings.create.assert_called_once()
        call_args = mock_client.embeddings.create.call_args
        assert call_args.kwargs["model"] == "text-embedding-3-small"
        assert call_args.kwargs["input"] == "Test text for embedding"
        assert call_args.kwargs["dimensions"] == 1536

    def test_get_embedding_empty_text_raises(self, embedding_service):
        with pytest.raises(ValueError, match="Text cannot be empty"):
            embedding_service.get_embedding("")
        
        with pytest.raises(ValueError, match="Text cannot be empty"):
            embedding_service.get_embedding("   ")

    def test_get_embedding_invalid_dimensions_raises(self, embedding_service, mock_openai_class):
        mock_client = Mock()
        mock_openai_class.return_value = mock_client
        
        # Return embedding with wrong dimensions
        mock_embedding = [0.1] * 768  # Wrong: 768 instead of 1536
        mock_response = Mock()
        mock_data = Mock()
        mock_data.embedding = mock_embedding
        mock_response.data = [mock_data]
        
        mock_client.embeddings.create.return_value = mock_response

        with pytest.raises(ValueError, match="Expected embedding with 1536 dimensions, got 768"):
            embedding_service.get_embedding("Test text")

    def test_get_embedding_openai_error_propagates(self, embedding_service, mock_openai_class):
        from openai import APIError
        import httpx
        
        mock_client = Mock()
        mock_openai_class.return_value = mock_client
        
        request = httpx.Request("POST", "https://api.openai.com/v1/embeddings")
        mock_client.embeddings.create.side_effect = APIError("API Error", request=request, body=None)
        
        with pytest.raises(APIError):
            embedding_service.get_embedding("Test text")

    def test_get_embedding_strips_whitespace(self, embedding_service, mock_openai_class):
        mock_client = Mock()
        mock_openai_class.return_value = mock_client
        
        mock_embedding = [0.1] * 1536
        mock_response = Mock()
        mock_data = Mock()
        mock_data.embedding = mock_embedding
        mock_response.data = [mock_data]
        
        mock_client.embeddings.create.return_value = mock_response

        result = embedding_service.get_embedding("  Text with spaces  ")

        assert result == mock_embedding
        call_args = mock_client.embeddings.create.call_args
        assert call_args.kwargs["input"] == "Text with spaces"