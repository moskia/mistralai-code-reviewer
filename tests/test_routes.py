import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_review_endpoint():
    response = client.post(
        "/review",
        json={
            "assignment_description": "Test Assignment",
            "github_repo_url": "https://github.com/octocat/Hello-World",
            "candidate_level": "Junior",
        },
    )
    assert response.status_code == 200
    assert "Found Files" in response.json()
