import pytest
from unittest.mock import AsyncMock, patch
from app.services.github_service import fetch_repo_contents
from app.services import ai_service

@pytest.mark.asyncio
async def test_fetch_repo_contents():
    """
    Test that fetch_repo_contents correctly fetches repo files from GitHub.
    This mocks httpx.AsyncClient.get to avoid real network calls.
    """
    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        # Mock response object
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [{"name": "README"}]
        mock_get.return_value.__aenter__.return_value = mock_response

        repo_contents = await fetch_repo_contents("https://github.com/test/test-repo")
        assert len(repo_contents) == 1
        assert repo_contents[0]["name"] == "README"


@pytest.mark.asyncio
async def test_generate_review():
    """
    Test that generate_review returns the expected review string.
    This mocks the AI client so no real API call is made.
    """
    mock_repo_contents = [{"name": "README"}]

    # Patch the AI client
    async def fake_complete(*args, **kwargs):
        class FakeChoice:
            class Message:
                content = "## Review Results\n--start--\n- `README`\n--end--\nMocked review content"
            message = Message()
        class FakeResponse:
            choices = [FakeChoice()]
        return FakeResponse()

    with patch.object(ai_service.client.chat, "complete", new=fake_complete):
        review = await ai_service.generate_review("Test assignment", mock_repo_contents, "Junior")
        assert "Mocked review content" in review
        assert "- `README`" in review

