from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_review_endpoint_json(monkeypatch):
    def fake_fetch_repo_and_generate_message(url: str) -> str:
        return "# Repository Files\n- `README.md`\n```hello```"
    async def fake_generate_review(*args, **kwargs) -> str:
        return (
            '{"files_found":["README.md"],'
            '"rating_out_of_5":4,'
            '"summary":"Looks good overall.",'
            '"findings":[{"file":"README.md","line":1,"severity":"low","issue":"Minor typo","suggestion":"Fix typo"}],'
            '"conclusion":"Ready to proceed."}'
        )
    monkeypatch.setattr("app.routes.fetch_repo_and_generate_message", fake_fetch_repo_and_generate_message)
    monkeypatch.setattr("app.routes.generate_review", fake_generate_review)

    resp = client.post("/review", json={
        "assignment_description": "Test",
        "github_repo_url": "https://github.com/octocat/Hello-World",
        "candidate_level": "Junior",
    })
    data = resp.json()
    assert resp.status_code == 200
    assert data["files_found"] == ["README.md"]
    assert data["rating_out_of_5"] == 4
    assert data["findings"][0]["severity"] == "low"

