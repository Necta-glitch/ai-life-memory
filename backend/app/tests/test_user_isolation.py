import pytest
from httpx import AsyncClient


class TestUserIsolation:
    @pytest.mark.asyncio
    async def test_user_a_cannot_see_user_b_memories(self, client: AsyncClient):
        await client.post("/memories/", json={"content": "User A memory"})

        response = await client.get("/memories/", headers={"X-User-ID": "user-b"})
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 0

    @pytest.mark.asyncio
    async def test_user_a_cannot_get_user_b_memory(self, client: AsyncClient):
        create_response = await client.post("/memories/", json={"content": "User A memory"})
        memory_id = create_response.json()["id"]

        response = await client.get(f"/memories/{memory_id}", headers={"X-User-ID": "user-b"})
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_user_a_cannot_update_user_b_memory(self, client: AsyncClient):
        create_response = await client.post("/memories/", json={"content": "User A memory"})
        memory_id = create_response.json()["id"]

        response = await client.put(
            f"/memories/{memory_id}",
            json={"content": "Hacked"},
            headers={"X-User-ID": "user-b"},
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_user_a_cannot_delete_user_b_memory(self, client: AsyncClient):
        create_response = await client.post("/memories/", json={"content": "User A memory"})
        memory_id = create_response.json()["id"]

        response = await client.delete(f"/memories/{memory_id}", headers={"X-User-ID": "user-b"})
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_user_isolation_with_query_param(self, client: AsyncClient):
        await client.post("/memories/", json={"content": "User A memory"})
        await client.post("/memories/", json={"content": "User B memory"}, headers={"X-User-ID": "user-b"})

        response_a = await client.get("/memories/")
        assert len(response_a.json()) == 1
        assert response_a.json()[0]["content"] == "User A memory"

        response_b = await client.get("/memories/", headers={"X-User-ID": "user-b"})
        assert len(response_b.json()) == 1
        assert response_b.json()[0]["content"] == "User B memory"