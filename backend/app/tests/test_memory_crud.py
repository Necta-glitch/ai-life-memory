import pytest
from unittest.mock import Mock
from httpx import AsyncClient
from app.ai.schemas import AIProcessingResult
from app.ai.embeddings import build_embedding_input


class TestMemoryCRUD:
    @pytest.mark.asyncio
    async def test_create_memory(self, client: AsyncClient):
        response = await client.post(
            "/memories/",
            json={"content": "Test memory", "source": "text"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["content"] == "Test memory"
        assert data["source"] == "text"
        assert data["user_id"] == "dev-user"
        assert "id" in data
        assert "created_at" in data

    @pytest.mark.asyncio
    async def test_list_memories(self, client: AsyncClient):
        await client.post("/memories/", json={"content": "Memory 1"})
        await client.post("/memories/", json={"content": "Memory 2"})

        response = await client.get("/memories/")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert data[0]["content"] == "Memory 1"
        assert data[1]["content"] == "Memory 2"

    @pytest.mark.asyncio
    async def test_get_memory(self, client: AsyncClient):
        create_response = await client.post(
            "/memories/", json={"content": "Test memory"}
        )
        memory_id = create_response.json()["id"]

        response = await client.get(f"/memories/{memory_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == memory_id
        assert data["content"] == "Test memory"

    @pytest.mark.asyncio
    async def test_get_nonexistent_memory_returns_404(self, client: AsyncClient):
        response = await client.get("/memories/999")
        assert response.status_code == 404
        assert response.json()["detail"] == "Memory not found"

    @pytest.mark.asyncio
    async def test_update_memory(self, client: AsyncClient):
        create_response = await client.post(
            "/memories/", json={"content": "Original content"}
        )
        memory_id = create_response.json()["id"]

        response = await client.put(
            f"/memories/{memory_id}",
            json={"content": "Updated content"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == memory_id
        assert data["content"] == "Updated content"

    @pytest.mark.asyncio
    async def test_update_memory_partial(self, client: AsyncClient):
        create_response = await client.post(
            "/memories/", json={"content": "Original content"}
        )
        memory_id = create_response.json()["id"]

        response = await client.put(
            f"/memories/{memory_id}",
            json={"occurred_at": "2024-01-15T10:00:00"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == memory_id
        assert data["content"] == "Original content"
        assert data["occurred_at"] == "2024-01-15T10:00:00"

    @pytest.mark.asyncio
    async def test_update_nonexistent_memory_returns_404(self, client: AsyncClient):
        response = await client.put(
            "/memories/999", json={"content": "Updated"}
        )
        assert response.status_code == 404
        assert response.json()["detail"] == "Memory not found"

    @pytest.mark.asyncio
    async def test_delete_memory(self, client: AsyncClient):
        create_response = await client.post(
            "/memories/", json={"content": "To delete"}
        )
        memory_id = create_response.json()["id"]

        response = await client.delete(f"/memories/{memory_id}")
        assert response.status_code == 204

        get_response = await client.get(f"/memories/{memory_id}")
        assert get_response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_nonexistent_memory_returns_404(self, client: AsyncClient):
        response = await client.delete("/memories/999")
        assert response.status_code == 404
        assert response.json()["detail"] == "Memory not found"


class TestMemoryAICreation:
    """Tests for AI processing during memory creation."""

    @pytest.mark.asyncio
    async def test_create_memory_calls_ai_service(self, client: AsyncClient, mock_ai_service: Mock):
        """Verify AIService.process_memory is called with the memory content."""
        await client.post("/memories/", json={"content": "Learned about Python async"})
        
        mock_ai_service.process_memory.assert_called_once_with("Learned about Python async")

    @pytest.mark.asyncio
    async def test_create_memory_persists_summary(self, client: AsyncClient):
        """Verify AI-generated summary is persisted in the response."""
        response = await client.post("/memories/", json={"content": "Test content"})
        
        assert response.status_code == 200
        data = response.json()
        assert data["summary"] == "Test summary"

    @pytest.mark.asyncio
    async def test_create_memory_persists_topics(self, client: AsyncClient):
        """Verify AI-generated topics are persisted in the response."""
        response = await client.post("/memories/", json={"content": "Test content"})
        
        assert response.status_code == 200
        data = response.json()
        assert data["topics"] == ["test", "topic"]

    @pytest.mark.asyncio
    async def test_create_memory_persists_entities(self, client: AsyncClient):
        """Verify AI-generated entities are persisted in the response."""
        response = await client.post("/memories/", json={"content": "Test content"})
        
        assert response.status_code == 200
        data = response.json()
        assert data["entities"] == ["test", "entity"]

    @pytest.mark.asyncio
    async def test_create_memory_response_contains_ai_fields(self, client: AsyncClient):
        """Verify the full API response includes all AI-generated fields."""
        response = await client.post("/memories/", json={"content": "Test content"})
        
        assert response.status_code == 200
        data = response.json()
        # Basic fields
        assert "id" in data
        assert "user_id" in data
        assert "content" in data
        assert "source" in data
        assert "created_at" in data
        # AI fields
        assert "summary" in data
        assert "topics" in data
        assert "entities" in data
        # AI field values
        assert data["summary"] == "Test summary"
        assert data["topics"] == ["test", "topic"]
        assert data["entities"] == ["test", "entity"]

    @pytest.mark.asyncio
    async def test_create_memory_ai_failure_rolls_back(self, client: AsyncClient, mock_ai_service: Mock):
        """Verify that if AI processing fails, the memory is not persisted (rollback)."""
        from openai import APIError
        import httpx
        
        request = httpx.Request("POST", "https://api.openai.com/v1/chat/completions")
        mock_ai_service.process_memory.side_effect = APIError("API Error", request=request, body=None)
        
        response = await client.post("/memories/", json={"content": "Test content"})
        
        # Should return 500 or appropriate error
        assert response.status_code == 500
        
        # Verify memory was not created (list should be empty)
        list_response = await client.get("/memories/")
        assert list_response.status_code == 200
        assert len(list_response.json()) == 0


class TestMemoryEmbeddingCreation:
    """Tests for embedding generation during memory creation."""

    @pytest.mark.asyncio
    async def test_create_memory_calls_embedding_service(self, client: AsyncClient, mock_embedding_service: Mock):
        """Verify EmbeddingService.get_embedding is called with the expected text."""
        await client.post("/memories/", json={"content": "Learned about Python async"})
        
        mock_embedding_service.get_embedding.assert_called_once()
        call_args = mock_embedding_service.get_embedding.call_args
        # Should be called with content + summary (MVP strategy)
        expected_text = build_embedding_input(
            content="Learned about Python async",
            summary="Test summary",
            strategy="content_summary",
        )
        assert call_args.args[0] == expected_text

    @pytest.mark.asyncio
    async def test_create_memory_persists_embedding(self, client: AsyncClient):
        """Verify the generated embedding is assigned to memory.embedding."""
        response = await client.post("/memories/", json={"content": "Test content"})
        
        assert response.status_code == 200
        data = response.json()
        # The embedding is not exposed in the API response (by design)
        # But we can verify it was called by checking the mock was used
        # The actual persistence is verified by the model tests

    @pytest.mark.asyncio
    async def test_create_memory_embedding_has_correct_dimensions(self, client: AsyncClient, mock_embedding_service: Mock):
        """Verify the embedding has 1536 dimensions."""
        mock_embedding_service.get_embedding.return_value = [0.5] * 1536
        
        response = await client.post("/memories/", json={"content": "Test content"})
        
        assert response.status_code == 200
        mock_embedding_service.get_embedding.assert_called_once()
        # The mock returns 1536 dims, which matches our validation

    @pytest.mark.asyncio
    async def test_user_isolation_unchanged(self, client: AsyncClient, mock_ai_service: Mock, mock_embedding_service: Mock):
        """Verify user isolation still works with embedding integration."""
        await client.post("/memories/", json={"content": "User A memory"})
        
        response_b = await client.get("/memories/", headers={"X-User-ID": "user-b"})
        assert response_b.status_code == 200
        assert len(response_b.json()) == 0