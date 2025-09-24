import json
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def _set_mocks(monkeypatch, ai_text, repo_contents="# Repository Files\n- `x`"):
    def fake_fetch_repo_and_generate_message(url: str) -> str:
        # Include "truncated" keyword optionally to test flag
        return repo_contents
    async def fake_generate_review(*args, **kwargs) -> str:
        return ai_text
    monkeypatch.setattr("app.routes.fetch_repo_and_generate_message", fake_fetch_repo_and_generate_message)
    monkeypatch.setattr("app.routes.generate_review", fake_generate_review)


def test_route_parses_plain_json(monkeypatch):
    data = {
        "files_found": ["a.py"],
        "rating_out_of_5": 5,
        "summary": "ok",
        "findings": [],
        "conclusion": "done"
    }
    _set_mocks(monkeypatch, json.dumps(data))
    r = client.post("/review", json={"assignment_description":"x", "github_repo_url":"https://github.com/o/r", "candidate_level":"Junior"})
    assert r.status_code == 200
    body = r.json()
    assert body["files_found"] == ["a.py"]
    assert body["raw_text"] is None  # not present on success


def test_route_parses_fenced_json(monkeypatch):
    fenced = "```json\n" + json.dumps({"files_found": [], "rating_out_of_5": 3, "summary": "ok", "findings": [], "conclusion": "x"}) + "\n```"
    _set_mocks(monkeypatch, fenced)
    r = client.post("/review", json={"assignment_description":"x", "github_repo_url":"https://github.com/o/r", "candidate_level":"Junior"})
    assert r.status_code == 200
    assert r.json()["rating_out_of_5"] == 3


def test_route_parses_double_encoded_json_and_sets_truncated(monkeypatch):
    inner = {"files_found": ["b.py"], "rating_out_of_5": 4, "summary": "ok", "findings": [], "conclusion": "x"}
    double_encoded = json.dumps(json.dumps(inner))  # JSON string
    repo_contents = "# Repository Files\n- `x`\n*(truncated: 10 files, 1000 bytes; limits reached)*"
    _set_mocks(monkeypatch, double_encoded, repo_contents=repo_contents)
    r = client.post("/review", json={"assignment_description":"x", "github_repo_url":"https://github.com/o/r", "candidate_level":"Junior"})
    body = r.json()
    assert body["truncated"] is True
    assert body["included_files"] == 1
    assert "(Note: analysis truncated" in body["summary"]

