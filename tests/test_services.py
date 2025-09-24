import os
import json
import pytest
import app.services.ai_service as ai


class FakeClient:
    class Msg:
        def __init__(self, content):
            self.content = content
    class Choice:
        def __init__(self, content):
            self.message = FakeClient.Msg(content)
    class Resp:
        def __init__(self, content):
            self.choices = [FakeClient.Choice(content)]
    def chat(self):  # pragma: no cover
        pass
    def complete(self, **kwargs):  # pragma: no cover
        return FakeClient.Resp("```json\n" + json.dumps({"files_found": [], "rating_out_of_5": 4, "summary": "ok", "findings": [], "conclusion": "x"}) + "\n```")


async def test_generate_review_strips_fences_and_returns_string(monkeypatch):
    monkeypatch.setenv("MISTRAL_API_KEY", "fake")
    # bypass real client
    monkeypatch.setattr(ai, "_client", FakeClient())
    out = await ai.generate_review("a", "b", "Junior")
    # Should be parseable JSON (still a string here)
    json.loads(out)


