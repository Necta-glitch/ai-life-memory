import pytest
from httpx import AsyncClient


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