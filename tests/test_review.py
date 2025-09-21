import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch
from app.main import app
from app.services import ai_service, github_service

client = TestClient(app)

# --------------------------
# 1️⃣ Test GitHub Service
# --------------------------
@pytest.mark.asyncio
async def test_fetch_repo_contents():
    # Mock your fetch_repo_contents to not call real GitHub
    fake_files = [
        {"name": "main.py", "path": "main.py", "download_url": "https://fakeurl.com/main.py", "type": "file"},
        {"name": "utils.py", "path": "utils.py", "download_url": "https://fakeurl.com/utils.py", "type": "file"}
    ]

    with patch("app.services.github_service.fetch_repo_contents", new_callable=AsyncMock) as mock_fetch:
        mock_fetch.return_value = fake_files
        result = await github_service.fetch_repo_contents("https://github.com/aminebenkia/test-repo", headers={})
        assert len(result) == 2
        assert result[0]["name"] == "main.py"

# --------------------------
# 2️⃣ Test AI Service
# --------------------------
@pytest.mark.asyncio
async def test_generate_review():
    mock_repo_contents = "def hello():\n    print('Hello world')"

    # Patch Mistral client call
    with patch("app.services.ai_service.client.chat.complete", new_callable=AsyncMock) as mock_mistral:
        # Fake Mistral response structure
        class FakeResponse:
            class Choice:
                class Message:
                    content = "## Review Results\nTest review content"
                message = Message()
            choices = [Choice()]

        mock_mistral.return_value = FakeResponse()

        review = await ai_service.generate_review("Build a REST API", mock_repo_contents, "Junior")
        assert "Test review content" in review

# --------------------------
# 3️⃣ Test FastAPI Route
# --------------------------
def test_review_endpoint(monkeypatch):
    # Mock AI service so it doesn’t call Mistral
    async def fake_generate_review(assignment_description, repo_contents, candidate_level):
        return "## Review Results\nMocked review content"

    monkeypatch.setattr(ai_service, "generate_review", fake_generate_review)

    response = client.post("/review", json={
        "assignment_description": "Build a REST API",
        "github_repo_url": "https://github.com/moskia/test-repo",
        "candidate_level": "Junior"
    })

    assert response.status_code == 200
    data = response.json()
    assert "files_found" in data
    assert "result" in data
    assert "Mocked review content" in data["result"]

