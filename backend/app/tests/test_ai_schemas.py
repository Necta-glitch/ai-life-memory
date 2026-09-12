import pytest
from app.ai.schemas import AIProcessingResult


class TestAIProcessingResult:
    def test_valid_ai_result_minimal(self):
        result = AIProcessingResult(
            summary="Learned about async programming",
            topics=["Python", "async"],
            entities=["Python", "asyncio"],
        )
        assert result.summary == "Learned about async programming"
        assert result.topics == ["Python", "async"]
        assert result.entities == ["Python", "asyncio"]

    def test_empty_topics_and_entities_allowed(self):
        result = AIProcessingResult(
            summary="Just a note",
            topics=[],
            entities=[],
        )
        assert result.topics == []
        assert result.entities == []

    def test_none_topics_and_entities_coerced_to_empty_list(self):
        result = AIProcessingResult(
            summary="Test",
            topics=None,
            entities=None,
        )
        assert result.topics == []
        assert result.entities == []

    def test_summary_whitespace_stripped(self):
        result = AIProcessingResult(
            summary="  Whitespace trimmed  ",
            topics=["test"],
            entities=["test"],
        )
        assert result.summary == "Whitespace trimmed"

    def test_invalid_summary_empty_raises(self):
        with pytest.raises(ValueError, match="String should have at least 1 character"):
            AIProcessingResult(summary="", topics=[], entities=[])

    def test_invalid_summary_whitespace_only_raises(self):
        with pytest.raises(ValueError, match="Summary cannot be empty"):
            AIProcessingResult(summary="   ", topics=[], entities=[])

    def test_invalid_topics_not_list_raises(self):
        with pytest.raises(ValueError, match="Must be a list"):
            AIProcessingResult(summary="Test", topics="not a list", entities=[])

    def test_invalid_entities_not_list_raises(self):
        with pytest.raises(ValueError, match="Must be a list"):
            AIProcessingResult(summary="Test", topics=[], entities="not a list")

    def test_invalid_topics_non_string_items_raises(self):
        with pytest.raises(ValueError):
            AIProcessingResult(summary="Test", topics=[1, 2], entities=[])

    def test_invalid_entities_non_string_items_raises(self):
        with pytest.raises(ValueError):
            AIProcessingResult(summary="Test", topics=[], entities=[{"name": "test"}])