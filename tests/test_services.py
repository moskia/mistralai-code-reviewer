# tests/test_services.py
import json
import pytest
import app.services.ai_service as ai


class FakeChat:
    def complete(self, **kwargs):
        # Return a structure that matches what ai_service expects
        payload = {
            "files_found": [],
            "rating_out_of_5": 4,
            "summary": "ok",
            "findings": [],
            "conclusion": "x",
        }
        content = "```json\n" + json.dumps(payload) + "\n```"
        return FakeResponse(content)


class FakeResponse:
    class Choice:
        class Msg:
            def __init__(self, content):
                self.content = content

        def __init__(self, content):
            self.message = FakeResponse.Choice.Msg(content)

    def __init__(self, content):
        self.choices = [FakeResponse.Choice(content)]


class FakeClient:
    def __init__(self):
        # mimic the real API: client.chat.complete(...)
        self.chat = FakeChat()


@pytest.mark.asyncio
async def test_generate_review_strips_fences_and_returns_string(monkeypatch):
    # Avoid creating a real Mistral client
    monkeypatch.setenv("MISTRAL_API_KEY", "fake")
    monkeypatch.setattr(ai, "_client", FakeClient())

    out = await ai.generate_review("a", "b", "Junior")
    # should be valid JSON string (fences removed in ai_service)
    json.loads(out)

