import json
from types import SimpleNamespace

import app.services.github_service as gh
from app.config import PREVIEW_LINES, MAX_FILE_BYTES


class FakeResp:
    def __init__(self, status=200, data=None, text=None):
        self.status_code = status
        self._data = data
        self._text = text

    def json(self):
        return self._data

    @property
    def text(self):
        return self._text if self._text is not None else json.dumps(self._data or {})

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError(f"http {self.status_code}")


def test_fetch_repo_prioritizes_code_and_applies_caps(monkeypatch):
    """Tree has code + meta + ignored dirs + oversize; ensure only expected make it in."""
    # 1) Repo exists
    def fake_get_repo(url, headers=None, timeout=None):
        assert "/repos/" in url
        return FakeResp(200, {"id": 1})

    # 2) Tree listing
    tree = [
        {"path": "node_modules/lib.js", "type": "blob", "size": 10},               # ignored dir
        {"path": "src/app.py", "type": "blob", "size": 50},                        # code (allowed)
        {"path": "README.md", "type": "blob", "size": 50},                         # meta (secondary)
        {"path": "big/binary.bin", "type": "blob", "size": MAX_FILE_BYTES + 1},    # oversized
        {"path": ".github/workflows/test.yml", "type": "blob", "size": 50},        # secondary
    ]
    def fake_get_tree(url, headers=None, timeout=None):
        assert "/git/trees/" in url
        return FakeResp(200, {"tree": tree})

    # 3) Contents API for selected paths
    def fake_session_get(self, url, timeout=None):
        if "src/app.py" in url:
            content = "print('hello')\n" * (PREVIEW_LINES + 5)  # longer than preview
            return FakeResp(200, {"encoding": "base64", "content": content.encode("utf-8").hex(), "size": len(content)})
        if "README.md" in url or "test.yml" in url:
            return FakeResp(200, {"encoding": "base64", "content": "hello".encode("utf-8").hex(), "size": 5})
        return FakeResp(404, {})

    # Patch requests + session
    monkeypatch.setattr("requests.get", lambda url, headers=None, timeout=None:
                        fake_get_repo(url, headers, timeout) if "/repos/" in url and "/git/trees/" not in url
                        else fake_get_tree(url, headers, timeout))
    monkeypatch.setattr("requests.Session.get", fake_session_get)

    # Execute
    out = gh.fetch_repo_and_generate_message("https://github.com/owner/repo")
    # Code file first, then meta; ignored/oversized not present
    assert "- `src/app.py`" in out
    assert out.index("`src/app.py`") < out.index("`README.md`")
    assert "node_modules" not in out
    assert "binary.bin" not in out
    # Preview truncated to PREVIEW_LINES
    snippet = out.split("```")[1]
    assert len(snippet.splitlines()) == PREVIEW_LINES


def test_fetch_repo_404(monkeypatch):
    def fake_get(url, headers=None, timeout=None):
        if "/repos/" in url and "/git/trees/" not in url:
            return FakeResp(404, {})
        return FakeResp(200, {"tree": []})
    monkeypatch.setattr("requests.get", fake_get)
    try:
        gh.fetch_repo_and_generate_message("https://github.com/owner/missing")
        assert False, "expected HTTPException for missing repo"
    except Exception as e:
        assert "Repository not found" in str(e) or "404" in str(e)

