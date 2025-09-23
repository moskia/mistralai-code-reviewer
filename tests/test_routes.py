def test_review_endpoint(monkeypatch):
    from fastapi.testclient import TestClient
    from app.main import app

    client = TestClient(app)

    # Mock repo fetch to return only README
    def fake_fetch_repo_and_generate_message(url):
        return "- `README`"

    # Patch the function in routes
    monkeypatch.setattr("app.routes.fetch_repo_and_generate_message", fake_fetch_repo_and_generate_message)

    response = client.post("/review", json={
        "assignment_description": "Test Assignment",
        "github_repo_url": "https://github.com/octocat/Hello-World",
        "candidate_level": "Junior",
    })

    assert response.status_code == 200
    data = response.json()

    # Since repo only has README
    assert data["files_found"] == ["`README`"]
    # Check that the result contains a mention of "README" and "no code"
    assert "README" in data["result"]
    assert "no actual code" in data["result"]

