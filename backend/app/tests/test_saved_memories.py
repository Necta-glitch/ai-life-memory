import pytest
from httpx import AsyncClient


class TestSavedMemoriesCreate:
    """Tests for POST /memories/{memory_id}/save"""

    @pytest.mark.asyncio
    async def test_user_can_save_own_memory(self, client: AsyncClient):
        """User can save their own memory."""
        # Create a memory
        create_response = await client.post("/memories/", json={"content": "Memory to save"})
        memory_id = create_response.json()["id"]

        # Save the memory
        response = await client.post(f"/memories/{memory_id}/save")
        assert response.status_code == 201
        data = response.json()
        assert data["status"] == "saved"
        assert data["memory_id"] == memory_id

    @pytest.mark.asyncio
    async def test_saved_memory_is_persisted(self, client: AsyncClient):
        """SavedMemory is persisted in database."""
        create_response = await client.post("/memories/", json={"content": "Memory to save"})
        memory_id = create_response.json()["id"]

        await client.post(f"/memories/{memory_id}/save")

        # Verify it appears in saved memories
        response = await client.get("/memories/saved")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["id"] == memory_id

    @pytest.mark.asyncio
    async def test_save_memory_response_correct(self, client: AsyncClient):
        """Save memory returns correct response format."""
        create_response = await client.post("/memories/", json={"content": "Test memory"})
        memory_id = create_response.json()["id"]

        response = await client.post(f"/memories/{memory_id}/save")
        assert response.status_code == 201
        data = response.json()
        assert data["status"] == "saved"
        assert data["memory_id"] == memory_id

    @pytest.mark.asyncio
    async def test_saving_same_memory_twice_no_duplicate(self, client: AsyncClient):
        """Saving the same memory twice does not create duplicates."""
        create_response = await client.post("/memories/", json={"content": "Test memory"})
        memory_id = create_response.json()["id"]

        # Save first time
        response1 = await client.post(f"/memories/{memory_id}/save")
        assert response1.status_code == 201

        # Save second time
        response2 = await client.post(f"/memories/{memory_id}/save")
        assert response2.status_code == 201

        # Verify only one saved memory exists
        response = await client.get("/memories/saved")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1


class TestSavedMemoriesDelete:
    """Tests for DELETE /memories/{memory_id}/save"""

    @pytest.mark.asyncio
    async def test_user_can_unsave_own_memory(self, client: AsyncClient):
        """User can unsave their own saved memory."""
        create_response = await client.post("/memories/", json={"content": "Memory to unsave"})
        memory_id = create_response.json()["id"]

        await client.post(f"/memories/{memory_id}/save")

        response = await client.delete(f"/memories/{memory_id}/save")
        assert response.status_code == 204

    @pytest.mark.asyncio
    async def test_unsave_removes_saved_memory(self, client: AsyncClient):
        """Unsave removes the saved memory from list."""
        create_response = await client.post("/memories/", json={"content": "Memory to unsave"})
        memory_id = create_response.json()["id"]

        await client.post(f"/memories/{memory_id}/save")
        await client.delete(f"/memories/{memory_id}/save")

        response = await client.get("/memories/saved")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 0

    @pytest.mark.asyncio
    async def test_unsave_not_saved_returns_404(self, client: AsyncClient):
        """Unsaving a memory that is not saved returns 404."""
        create_response = await client.post("/memories/", json={"content": "Not saved memory"})
        memory_id = create_response.json()["id"]

        response = await client.delete(f"/memories/{memory_id}/save")
        assert response.status_code == 404
        assert response.json()["detail"] == "Memory not found or not saved"


class TestSavedMemoriesList:
    """Tests for GET /memories/saved"""

    @pytest.mark.asyncio
    async def test_user_can_retrieve_saved_memories(self, client: AsyncClient):
        """User can retrieve their saved memories."""
        create_response = await client.post("/memories/", json={"content": "Memory 1"})
        memory_id = create_response.json()["id"]

        await client.post(f"/memories/{memory_id}/save")

        response = await client.get("/memories/saved")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["id"] == memory_id
        assert data[0]["content"] == "Memory 1"

    @pytest.mark.asyncio
    async def test_only_saved_memories_returned(self, client: AsyncClient):
        """Only saved memories are returned, not all memories."""
        # Create two memories
        create1 = await client.post("/memories/", json={"content": "Saved memory"})
        create2 = await client.post("/memories/", json={"content": "Not saved memory"})

        memory_id_1 = create1.json()["id"]

        # Save only the first one
        await client.post(f"/memories/{memory_id_1}/save")

        response = await client.get("/memories/saved")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["content"] == "Saved memory"

    @pytest.mark.asyncio
    async def test_multiple_saved_memories_returned(self, client: AsyncClient):
        """Multiple saved memories are returned."""
        create1 = await client.post("/memories/", json={"content": "Memory 1"})
        create2 = await client.post("/memories/", json={"content": "Memory 2"})
        create3 = await client.post("/memories/", json={"content": "Memory 3"})

        id1 = create1.json()["id"]
        id2 = create2.json()["id"]
        id3 = create3.json()["id"]

        await client.post(f"/memories/{id1}/save")
        await client.post(f"/memories/{id2}/save")

        response = await client.get("/memories/saved")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2

    @pytest.mark.asyncio
    async def test_ordering_newest_saved_first(self, client: AsyncClient):
        """Ordering is newest saved first."""
        create1 = await client.post("/memories/", json={"content": "First memory"})
        create2 = await client.post("/memories/", json={"content": "Second memory"})

        id1 = create1.json()["id"]
        id2 = create2.json()["id"]

        # Save first memory
        await client.post(f"/memories/{id1}/save")
        # Save second memory (more recent)
        await client.post(f"/memories/{id2}/save")

        response = await client.get("/memories/saved")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        # Most recently saved should be first
        assert data[0]["id"] == id2
        assert data[1]["id"] == id1

    @pytest.mark.asyncio
    async def test_empty_saved_list_returns_empty_array(self, client: AsyncClient):
        """Empty saved list returns empty array."""
        response = await client.get("/memories/saved")
        assert response.status_code == 200
        data = response.json()
        assert data == []


class TestSavedMemoriesUserIsolation:
    """Tests for user isolation in saved memories."""

    @pytest.mark.asyncio
    async def test_user_cannot_save_another_user_memory(self, client: AsyncClient):
        """User cannot save another user's memory."""
        # User A creates a memory
        create_response = await client.post("/memories/", json={"content": "User A memory"})
        memory_id = create_response.json()["id"]

        # User B tries to save it
        response = await client.post(
            f"/memories/{memory_id}/save",
            headers={"X-User-ID": "user-b"}
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_user_cannot_unsave_another_user_memory(self, client: AsyncClient):
        """User cannot unsave another user's saved memory."""
        # User A creates and saves a memory
        create_response = await client.post("/memories/", json={"content": "User A memory"})
        memory_id = create_response.json()["id"]
        await client.post(f"/memories/{memory_id}/save")

        # User B tries to unsave it
        response = await client.delete(
            f"/memories/{memory_id}/save",
            headers={"X-User-ID": "user-b"}
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_user_cannot_see_another_user_saved_memories(self, client: AsyncClient):
        """User cannot see another user's saved memories."""
        # User A creates and saves a memory
        create_response = await client.post("/memories/", json={"content": "User A saved memory"})
        memory_id = create_response.json()["id"]
        await client.post(f"/memories/{memory_id}/save")

        # User B tries to see saved memories
        response = await client.get("/memories/saved", headers={"X-User-ID": "user-b"})
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 0

    @pytest.mark.asyncio
    async def test_another_user_memory_not_exposed_through_saved(self, client: AsyncClient):
        """A memory belonging to another user is not exposed through saved endpoint."""
        # User A creates a memory
        create_response = await client.post("/memories/", json={"content": "User A memory"})
        memory_id = create_response.json()["id"]

        # User B tries to save it
        save_response = await client.post(
            f"/memories/{memory_id}/save",
            headers={"X-User-ID": "user-b"}
        )
        assert save_response.status_code == 404

        # User B's saved list should be empty
        response = await client.get("/memories/saved", headers={"X-User-ID": "user-b"})
        assert response.status_code == 200
        assert len(response.json()) == 0


class TestSavedMemoriesDatabaseIntegrity:
    """Tests for database integrity."""

    @pytest.mark.asyncio
    async def test_duplicate_user_memory_prevented_by_constraint(self, client: AsyncClient):
        """Duplicate (user_id, memory_id) rows are prevented by database constraint."""
        create_response = await client.post("/memories/", json={"content": "Test memory"})
        memory_id = create_response.json()["id"]

        # Save first time
        await client.post(f"/memories/{memory_id}/save")

        # Attempt to save again - should be idempotent, not create duplicate
        await client.post(f"/memories/{memory_id}/save")

        # Verify only one in database by checking saved list
        response = await client.get("/memories/saved")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1

    @pytest.mark.asyncio
    async def test_unsave_then_save_again_works(self, client: AsyncClient):
        """Unsave and then save again works correctly."""
        create_response = await client.post("/memories/", json={"content": "Test memory"})
        memory_id = create_response.json()["id"]

        # Save
        await client.post(f"/memories/{memory_id}/save")
        # Unsave
        await client.delete(f"/memories/{memory_id}/save")
        # Save again
        await client.post(f"/memories/{memory_id}/save")

        response = await client.get("/memories/saved")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["id"] == memory_id