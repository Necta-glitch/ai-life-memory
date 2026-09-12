import pytest
from unittest.mock import Mock, MagicMock, patch, PropertyMock

from app.ai.service import AIService
from app.ai.schemas import AIProcessingResult


class TestAIService:
    @pytest.fixture
    def mock_openai_class(self):
        with patch("app.ai.service.OpenAI") as mock_class:
            yield mock_class

    @pytest.fixture
    def ai_service(self):
        return AIService(api_key="test-key", model="gpt-4o-mini")

    def test_init_with_explicit_params(self):
        service = AIService(api_key="explicit-key", model="gpt-4o")
        assert service.api_key == "explicit-key"
        assert service.model == "gpt-4o"

    def test_init_uses_config_defaults(self):
        with patch("app.ai.service.OPENAI_API_KEY", "config-key"), \
             patch("app.ai.service.OPENAI_MODEL", "config-model"):
            service = AIService()
            assert service.api_key == "config-key"
            assert service.model == "config-model"

    def test_client_property_creates_client_once(self, ai_service, mock_openai_class):
        mock_client = Mock()
        mock_openai_class.return_value = mock_client
        
        client1 = ai_service.client
        client2 = ai_service.client
        assert client1 is client2
        assert client1 is mock_client
        mock_openai_class.assert_called_once_with(api_key="test-key")

    def test_client_property_raises_without_api_key(self):
        with patch("app.ai.service.OPENAI_API_KEY", None):
            service = AIService(api_key=None)
            with pytest.raises(ValueError, match="OPENAI_API_KEY is not configured"):
                _ = service.client

    def test_process_memory_success(self, ai_service, mock_openai_class):
        mock_client = Mock()
        mock_openai_class.return_value = mock_client
        
        mock_parsed = AIProcessingResult(
            summary="Test summary",
            topics=["Python", "async"],
            entities=["Python", "asyncio"],
        )
        
        mock_response = Mock()
        mock_choice = Mock()
        mock_choice.message.parsed = mock_parsed
        mock_response.choices = [mock_choice]
        
        mock_client.beta.chat.completions.parse.return_value = mock_response

        result = ai_service.process_memory("Test content")

        assert isinstance(result, AIProcessingResult)
        assert result.summary == "Test summary"
        assert result.topics == ["Python", "async"]
        assert result.entities == ["Python", "asyncio"]

        mock_client.beta.chat.completions.parse.assert_called_once()
        call_args = mock_client.beta.chat.completions.parse.call_args
        assert call_args.kwargs["model"] == "gpt-4o-mini"
        assert call_args.kwargs["response_format"] is AIProcessingResult
        assert call_args.kwargs["temperature"] == 0.3
        messages = call_args.kwargs["messages"]
        assert len(messages) == 2
        assert messages[0]["role"] == "system"
        assert messages[1]["role"] == "user"
        assert "Test content" in messages[1]["content"]

    def test_process_memory_empty_content_raises(self, ai_service):
        with pytest.raises(ValueError, match="Content cannot be empty"):
            ai_service.process_memory("")
        
        with pytest.raises(ValueError, match="Content cannot be empty"):
            ai_service.process_memory("   ")

    def test_process_memory_openai_error_propagates(self, ai_service, mock_openai_class):
        from openai import APIError
        import httpx
        
        mock_client = Mock()
        mock_openai_class.return_value = mock_client
        
        request = httpx.Request("POST", "https://api.openai.com/v1/chat/completions")
        mock_client.beta.chat.completions.parse.side_effect = APIError("API Error", request=request, body=None)
        
        with pytest.raises(APIError):
            ai_service.process_memory("Test content")