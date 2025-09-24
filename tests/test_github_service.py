# tests/test_github_service.py
import base64
import json

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
        {"path": "node_modules/lib.js", "type": "blob", "size": 10},                # ignored dir
        {"path": "src/app.py", "type": "blob", "size": 50},                         # code (allowed)
        {"path": "README.md", "type": "blob", "size": 50},                          # meta (secondary)
        {"path": "big/binary.bin", "type": "blob", "size": MAX_FILE_BYTES + 1},     # oversized
        {"path": ".github/workflows/test.yml", "type": "blob", "size": 50},         # secondary
    ]

    def fake_get_tree(url, headers=None, timeout=None):
        assert "/git/trees/" in url
        return FakeResp(200, {"tree": tree})

    # 3) Contents API for selected paths (use REAL base64 like GitHub)
    def fake_session_get(self, url, timeout=None):
        if "src/app.py" in url:
            content = "print('hello')\n" * (PREVIEW_LINES + 5)  # longer than preview
            b64 = base64.b64encode(content.encode("utf-8")).decode("utf-8")
            return FakeResp(200, {"encoding": "base64", "content": b64, "size": len(content)})

        if "README.md" in url or "test.yml" in url:
            b64_small = base64.b64encode(b"hello").decode("utf-8")
            return FakeResp(200, {"encoding": "base64", "content": b64_small, "size": 5})

        return FakeResp(404, {})

    # Patch requests + session
    def _router_get(url, headers=None, timeout=None):
        # route to repo or tree
        if "/repos/" in url and "/git/trees/" not in url:
            return fake_get_repo(url, headers, timeout)
        return fake_get_tree(url, headers, timeout)

    monkeypatch.setattr("requests.get", _router_get)
    monkeypatch.setattr("requests.Session.get", fake_session_get)

    # Execute
    out = gh.fetch_repo_and_generate_message("https://github.com/owner/repo")

    # Code file first, then meta; ignored/oversized not present
    assert "- `src/app.py`" in out
    assert "node_modules" not in out
    assert "binary.bin" not in out
    assert out.index("`src/app.py`") < out.index("`README.md`")

    # Preview truncated to PREVIEW_LINES
    # The first fenced code block appears right after src/app.py
    blocks = out.split("```")
    assert len(blocks) >= 3
    snippet = blocks[1]  # content of the first code fence
    assert len(snippet.splitlines()) <= PREVIEW_LINES


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

